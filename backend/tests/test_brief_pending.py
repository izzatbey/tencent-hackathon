#!/usr/bin/env python3
"""Spesifikasi yang bisa dijalankan untuk test case brief yang fiturnya belum ada.

Setiap tes yang ditandai `expectedFailure` adalah kontrak untuk fitur yang
belum dibangun. Begitu fiturnya ada dan tesnya lulus, Python melaporkan
"unexpected success": cabut dekoratornya, dan tes itu menjadi regresi biasa.
Per 28 Okt semua kasus di sini lulus: #2, #6, #9, #10, #14, #18 lewat
backend/scripts/ask_bridge.py (klarifikasi + pratinjau aturan, tanpa LLM) dan
#19 lewat S5 Pra-CAB.

Asersinya sengaja tidak mengikat bentuk field baru: yang diperiksa adalah
isi payload publik (nama, zona waktu, doc_id) yang harus muncul apa pun
bentuk kontraknya nanti. Oracle diambil dari berkas data di
knowledge-base/source/, bukan dari kode yang dites.

Nomor "#n" merujuk ke test matrix adjusted_brief.md §6.
"""

import csv
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "knowledge-base" / "source"
sys.path.insert(0, str(ROOT / "backend" / "api"))

import server  # noqa: E402

QUESTIONS = {q["q_id"]: q["raw_text"] for q in map(
    json.loads, (SOURCE / "questions.jsonl").read_text(encoding="utf-8").splitlines()) }
with (SOURCE / "contacts.csv").open(encoding="utf-8-sig", newline="") as fh:
    CONTACTS = list(csv.DictReader(fh))
with (SOURCE / "cmdb.csv").open(encoding="utf-8-sig", newline="") as fh:
    CMDB = list(csv.DictReader(fh))


class BriefCase(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sahabat-brief-"))
        self._old = os.environ.get("SECURITY_SAHABAT_AUDIT_LOG")
        os.environ["SECURITY_SAHABAT_AUDIT_LOG"] = str(self.tmp / "audit.jsonl")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("SECURITY_SAHABAT_AUDIT_LOG", None)
        else:
            os.environ["SECURITY_SAHABAT_AUDIT_LOG"] = self._old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ask(self, q_id, user, question=None):
        return server.ask(question or QUESTIONS[q_id], user=user)


class PendingBriefTest(BriefCase):

    def test_02_firmware_makassar_mengutip_jendela_wms_dan_salat_jumat(self):  # #2
        """Given Ragil menanyakan upgrade firmware fw-edge-mks-01 "Jumat siang",
        when ia bertanya, then bukti memuat jendela replikasi WMS (TOPO-WMS-WINDOW)
        dan waktu salat Jumat (TOPO-PRAYER-TIMES), dan jawaban menawarkan jendela lain.
        Lulus sejak 28 Okt lewat ask_bridge: klarifikasi zona waktu + jam salat dari
        register (POL-w001/w002) dan pratinjau aturan untuk fw-edge-mks-01."""
        response = self.ask("Q-002", "Ragil Wibowo")
        ids = {c["doc_id"] for c in response["citations"]}
        self.assertLessEqual({"TOPO-WMS-WINDOW", "TOPO-PRAYER-TIMES"}, ids)
        self.assertIsNotNone(response["answer"])

    def test_06_konflik_sop_7_dengan_memo_oktober_dari_chat(self):  # #6
        """Given memo Oktober ada di chat_exports.jsonl, when Ragil bertanya Q-010,
        then kedua sumber dikutip dengan tanggalnya dan memo terbaru yang dipakai.
        Lulus sejak 28 Okt: memo dikutip lewat aturan register POL-m001 (pratinjau
        ask_bridge), bukan lewat indeks chat export."""
        response = self.ask("Q-010", "Ragil Wibowo")
        sources = {c["doc_id"] for c in response["citations"]}
        self.assertIn("SOP-7", sources)
        self.assertTrue(any(s.upper().startswith(("CHAT", "MSG", "MEMO")) for s in sources), sources)

    def test_09_dua_budi_memicu_klarifikasi_dengan_peran_dan_lokasi(self):  # #9
        """Given contacts.csv punya dua Budi, when Dewi meminta "kirim ke Pak Budi",
        then sistem bertanya Budi yang mana, menyebut nama lengkap, peran, dan lokasi keduanya."""
        budis = [c for c in CONTACTS if c["name"].split()[0] == "Budi"]
        self.assertEqual(len(budis), 2, "oracle berubah: contacts.csv harus punya dua Budi")
        text = json.dumps(self.ask("Q-005", "Dewi Anggraini"), ensure_ascii=False)
        for budi in budis:
            self.assertIn(budi["name"], text)
            self.assertIn(budi["office"], text)

    def test_10_jumat_siang_minta_kejelasan_wib_atau_wita(self):  # #10
        """Given dua Budi berada di zona WIB dan WITA, when Dewi minta jadwal "Jumat siang",
        then sistem menanyakan zona waktunya dan menghindari jam salat Jumat."""
        text = json.dumps(self.ask("Q-005", "Dewi Anggraini"), ensure_ascii=False)
        self.assertIn("WIB", text)
        self.assertIn("WITA", text)
        self.assertIsNotNone(self.ask("Q-005", "Dewi Anggraini")["answer"])

    def test_14_server_yang_itu_meminta_klarifikasi(self):  # #14
        """Given Bimo menulis "server yang itu di gudang Makassar", when ia bertanya,
        then sistem tidak menebak, tetapi menyebut kandidat aset Makassar dari CMDB
        dan bertanya yang mana."""
        candidates = [a["asset_id"] for a in CMDB if a["site"] == "Makassar"]
        self.assertGreaterEqual(len(candidates), 2)
        response = self.ask("Q-012", "Bimo Nugroho")
        self.assertIsNotNone(response["answer"])
        mentioned = [a for a in candidates if a in response["answer"]]
        self.assertGreaterEqual(len(mentioned), 2, mentioned)

    def test_18_permintaan_aksi_tercatat_menunggu_approval(self):  # #18
        """Given Andini meminta aksi ("tolong buka port 22 sekarang"), when ia bertanya,
        then tidak ada yang dieksekusi dan audit log mencatat approval_state menunggu.
        Lulus sejak 28 Okt: ask_bridge mengenali kalimat perintah; pratinjau Pra-CAB
        memberi BLOCKED (EXPOSURE server-farm-jkt), dicatat approval_state blocked."""
        self.ask(None, "Andini Pratama",
                 question="Tolong bukakan port 22 dari internet ke db-erp-jkt-01 sekarang juga.")
        record = server.replay(json.loads((self.tmp / "audit.jsonl").read_text(
            encoding="utf-8").splitlines()[-1])["q_id"])[0]
        self.assertIn(record["approval_state"], {"pending", "blocked"})

    def test_19_undo_dalam_60_detik_setelah_approve(self):  # #19
        """Given aksi sudah di-approve, when user menekan undo dalam 60 detik,
        then eksekusi dibatalkan dan audit log mencatat undo.
        Lulus sejak 28 Okt lewat S5 Pra-CAB (bukan URL /api/approvals yang dulu
        ditebak spesifikasi ini): approve -> dispatch (mock) -> undo -> cab.undone."""
        httpd = server.make_server("127.0.0.1", 0)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        base = "http://127.0.0.1:%d" % httpd.server_address[1]

        def post(path, body):
            req = urllib.request.Request(base + path, data=json.dumps(body).encode("utf-8"), method="POST",
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as res:
                    return res.status, json.loads(res.read())
            except urllib.error.HTTPError as err:
                return err.code, json.loads(err.read())

        # perubahan LOW: satu approver (IT Admin), tanpa rapat CAB
        fields = {"title": "Ubah zona DNS internal", "assets": ["dns-jkt-01"], "change_kind": "config_change",
                  "production_impact": False, "description": "Tambah record A", "reason": "Server baru",
                  "impact": "-", "implementation_plan": "Edit zone file", "rollback_plan": "Kembalikan zone file",
                  "window": {"start": "2099-01-03T20:00:00+07:00", "end": "2099-01-03T21:00:00+07:00"}}
        try:
            _, cr = post("/api/requests", {"user": "Eka Putri", "fields": fields})
            post("/api/requests/%s/submit" % cr["id"], {"user": "Eka Putri"})
            post("/api/requests/%s/approve" % cr["id"], {"user": "Andini Pratama", "slot": "it_admin"})
            _, dispatched = post("/api/requests/%s/dispatch" % cr["id"], {"user": "Eka Putri"})
            self.assertTrue(all(a["status"] == "would_have_sent" for a in dispatched["dispatch"]["actions"]))
            status, undone = post("/api/requests/%s/undo" % cr["id"], {"user": "Eka Putri"})
            self.assertEqual((status, undone["state"]), (200, "undone"))
        finally:
            httpd.shutdown()
            httpd.server_close()
        stages = [json.loads(line)["stage"] for line in
                  (self.tmp / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(stages[-2:], ["cab.dispatched", "cab.undone"])


class AlreadyPassingBriefTest(BriefCase):

    def test_11_transkrip_suara_diproses_sama_dengan_ketikan(self):  # #11
        """Transkrip voice note ("[transcript] ...") menghasilkan bukti yang sama
        dengan teks yang diketik."""
        spoken = self.ask("Q-005", "Dewi Anggraini")
        typed = self.ask(None, "Dewi Anggraini", question=QUESTIONS["Q-005"].replace("[transcript] ", ""))
        self.assertEqual([c["doc_id"] for c in spoken["citations"]],
                         [c["doc_id"] for c in typed["citations"]])
        self.assertTrue(spoken["citations"])


if __name__ == "__main__":
    unittest.main()
