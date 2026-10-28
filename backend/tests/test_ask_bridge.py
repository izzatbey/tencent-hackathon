#!/usr/bin/env python3
"""Tes jembatan tanya-jawab -> Pra-CAB (backend/scripts/ask_bridge.py).

Risiko terbesar: menebak (orang, aset, zona waktu), menganggap pertanyaan
sebagai perintah, menyimpulkan "tidak boleh" tanpa aturan, dan membuat
jawaban yang berbeda untuk topik restricted vs fiktif.

    python -m unittest discover -s backend/tests -v
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
sys.path.insert(0, str(ROOT / "backend" / "api"))

import ask_bridge  # noqa: E402
import cab_api  # noqa: E402
import server  # noqa: E402

NOW = datetime.fromisoformat("2026-10-28T10:00:00+07:00")


def run(text, user=None, rules=None):
    return ask_bridge.analyze(text, user=user, rules=rules, now=NOW)


class ClarifyTest(unittest.TestCase):

    def test_nama_lengkap_tidak_diklarifikasi(self):
        self.assertEqual(run("Tolong kirim notulen ke Pak Budi Santoso.")["summary"]["clarify"], [])
        self.assertEqual(run("Tolong kirim notulen ke Pak Budi.")["summary"]["clarify"], ["person"])

    def test_nama_unik_tidak_diklarifikasi(self):
        self.assertEqual(run("Tolong kirim notulen ke Pak Joko.")["summary"]["clarify"], [])

    def test_jadwal_dengan_zona_tidak_diklarifikasi(self):
        self.assertEqual(run("Jadwalkan rapat Jumat 14:00 WIB.")["summary"]["clarify"], [])
        self.assertEqual(run("Jadwalkan rapat Jumat siang.")["summary"]["clarify"], ["timezone"])

    def test_waktu_tanpa_niat_menjadwalkan_tidak_diklarifikasi(self):
        r = run("Kenapa replikasi ke Jakarta sering ganggu jam 11 malem?")
        self.assertEqual(r["summary"]["clarify"], [])

    def test_salat_jumat_dari_register_dengan_kutipan(self):
        r = run("Bisakah upgrade firmware fw-edge-mks-01 Jumat siang?", user="Ragil Wibowo")
        text = " ".join(r["answer_parts"])
        self.assertIn("Makassar 11:00-12:30 WITA", text)
        self.assertIn("TOPO-PRAYER-TIMES", {c["doc_id"] for c in r["citations"]})
        # tanpa aturan salat aktif, tidak ada jam salat yang dikarang
        no_prayer = [x for x in __import__("policy_register").load_seed() if x["check_id"] != "FRIDAY-PRAYER"]
        self.assertNotIn("salat", " ".join(run("Bisakah upgrade firmware fw-edge-mks-01 Jumat siang?",
                                              user="Ragil Wibowo", rules=no_prayer)["answer_parts"]))

    def test_jenis_dan_site_yang_ambigu(self):
        r = run("Boleh buka port 443 dari internet ke database Jakarta?")
        self.assertEqual(r["summary"]["clarify"], ["asset"])
        self.assertIsNone(r["summary"]["preview"])  # tidak menebak aset mana yang dinilai
        text = " ".join(r["answer_parts"])
        self.assertIn("db-erp-jkt-01", text)
        self.assertIn("db-hr-jkt-01", text)

    def test_jenis_dan_site_yang_unik_dipetakan(self):
        r = run("Boleh remote ke firewall Makassar dari rumah?", user="Ragil Wibowo")
        self.assertEqual(r["summary"]["preview"]["rules"], ["POL-m001"])


class ActionTest(unittest.TestCase):

    def test_pertanyaan_bukan_perintah(self):
        for text in ("Boleh install Chrome di laptop kantor?", "Apakah boleh buka port 22 ke db-hr-jkt-01?",
                     "Kemarin mesin gudang mati, ingin tahu kenapa.", "Saya ingin jadwal yang lain."):
            with self.subTest(text=text):
                self.assertEqual(run(text)["approval_state"], "n/a")

    def test_perintah_tanpa_aset_menunggu(self):
        r = run("Tolong teruskan file ini ke semua staff.")
        self.assertEqual((r["approval_state"], r["summary"]["action"]), ("pending", True))
        self.assertIn("tidak ada yang dikirim", " ".join(r["answer_parts"]))

    def test_perintah_yang_dilarang_aturan_diblokir(self):
        r = run("Tolong bukakan SSH dari internet ke db-hr-jkt-01 sekarang.", user="Andini Pratama")
        self.assertEqual(r["approval_state"], "blocked")
        self.assertEqual(r["summary"]["preview"]["rules"], ["POL-x001"])


class VerdictTest(unittest.TestCase):

    def test_tidak_boleh_hanya_bila_ada_aturan_block(self):
        allowed = run("Boleh upgrade firmware dns-jkt-01?", user="Andini Pratama")
        self.assertIn("boleh diajukan", " ".join(allowed["answer_parts"]))
        self.assertNotIn("tidak boleh", " ".join(allowed["answer_parts"]))

    def test_akses_untuk_diri_sendiri_dinilai_dengan_departemen_penanya(self):
        r = run("Saya mau request akses ke db-erp-jkt-01.", user="Damar Saputra")
        self.assertEqual(r["summary"]["preview"]["outcome"], "BLOCKED")
        self.assertIn("Damar Saputra (External)", " ".join(r["answer_parts"]))

    def test_pertanyaan_umum_tidak_disentuh(self):
        for text in ("Password policy kita berapa bulan?", "Siapa owner Proyek Garuda?", "Boleh bawa kucing?"):
            with self.subTest(text=text):
                r = run(text)
                self.assertEqual((r["answer_parts"], r["flags"], r["approval_state"]), ([], [], "n/a"))


class OneBrainTest(unittest.TestCase):
    """Aturan yang disahkan di Pra-CAB langsung dipakai jawaban /api/ask."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bridge-"))
        self._old = os.environ.get("SECURITY_SAHABAT_AUDIT_LOG")
        os.environ["SECURITY_SAHABAT_AUDIT_LOG"] = str(self.tmp / "audit.jsonl")
        cab_api.CLOCK.set(NOW)

    def tearDown(self):
        cab_api.CLOCK.set(None)
        if self._old is None:
            os.environ.pop("SECURITY_SAHABAT_AUDIT_LOG", None)
        else:
            os.environ["SECURITY_SAHABAT_AUDIT_LOG"] = self._old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_aturan_baru_mengubah_jawaban_chat(self):
        question = "Saya mau request akses ke mail-jkt-01."
        before = server.ask(question, user="Eka Putri")
        self.assertIn("boleh diajukan", before["answer"])

        store = cab_api.store_for(self.tmp / "audit.jsonl")
        quote = "mail relay mail-jkt-01 hanya boleh diakses oleh tim IT"
        doc = store.policies.add_source(store.actor("Andini Pratama"), "Memo", "Mulai hari ini %s." % quote,
                                        "Citra Kusuma")
        rule = store.policies.propose(store.actor("Andini Pratama"), {
            "title": "Mail relay hanya untuk IT", "topic": "access_scope", "check_id": "ACCESS-SCOPE",
            "tier": "perusahaan", "subject": {"asset": "mail-jkt-01"}, "action": "access",
            "condition": {"grantee_department_not_in": ["IT"]}, "effect": "BLOCK",
            "message": "{grantee} ({department}) tidak boleh mengakses {asset}.",
            "sources": [{"type": "submitted", "doc_id": doc, "quote": quote}], "owner": "Citra Kusuma"})
        store.policies.approve(store.actor("Citra Kusuma"), rule["id"])

        after = server.ask(question, user="Eka Putri")
        self.assertIn("tidak boleh", after["answer"])
        self.assertIn("[%s]" % rule["id"], after["answer"])
        last = json.loads((self.tmp / "audit.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(last["bridge"]["preview"]["rules"], [rule["id"]])


if __name__ == "__main__":
    unittest.main()
