#!/usr/bin/env python3
"""Uji mutasi untuk penjaga keamanan (standar Coderoach: tiap penjaga dibuktikan).

Setiap mutan melumpuhkan satu penjaga, menjalankan tes yang seharusnya
menangkapnya, lalu memulihkan berkas. Semua baris harus MERAH; "LOLOS!" berarti
penjaga itu tidak dijaga tes apa pun.

    python tools/mutate_guards.py
"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENGINE = REPO / "backend/scripts/search_kb.py"
API = REPO / "backend/api/server.py"

MUTANTS = [
    ("zona disaring setelah pencarian (post-filter)", ENGINE,
     '    for doc in (r["doc"] for r in readable):', "    for doc in visible:",
     ["backend.tests.test_accountability.NonInterferenceTest.test_restricted_dan_zona_tertutup_tidak_mengubah_jawaban_siapa_pun"]),
    ("restricted terkunci ikut dinilai", ENGINE,
     'and (not is_restricted(d["meta"]) or d["path"] in unlocked)]', "]",
     ["backend.tests.test_accountability.NonInterferenceTest.test_dokumen_restricted_baru_dengan_kata_kunci_umum_tetap_tanpa_pengaruh"]),
    ("idf dari semua dokumen", ENGINE,
     'idf, _ = compute_idf([r["doc"] for r in readable])', "idf, _ = compute_idf(docs)",
     ["backend.tests.test_accountability.NonInterferenceTest.test_restricted_dan_zona_tertutup_tidak_mengubah_jawaban_siapa_pun"]),
    ("flag menyebut id yang tak terbaca", ENGINE,
     "        if readable is None or str(doc_id) in readable:", "        if True:",
     ["backend.tests.test_accountability.NonInterferenceTest.test_flag_tidak_menyebut_dokumen_yang_tak_boleh_dibaca"]),
    ("API menerima user apa pun", API,
     '    user = user if user in {p["user"] for p in personas()} else None', "    pass",
     ["backend.tests.test_api.IdentityTest"]),
    ("API membaca identitas dari teks", API,
     "                                         identity_from_text=False)", "                                         identity_from_text=True)",
     ["backend.tests.test_api.IdentityTest", "backend.tests.test_api.HttpTest.test_identitas_dari_body_bukan_dari_teks"]),
    ("audit gagal ditelan", API,
     "    write_log(record)\n", "    try:\n        write_log(record)\n    except OSError:\n        pass\n",
     ["backend.tests.test_api.AuditLogTest.test_log_gagal_ditulis_berarti_jawaban_tidak_dikirim"]),
    ("galat engine tidak dicatat", API,
     '                   "status": "ERROR"})', '                   "status": "ERROR"}) if False else None',
     ["backend.tests.test_api.AuditLogTest.test_galat_engine_tetap_tercatat"]),
    ("karakter tak terlihat dianggap isi", API,
     "not guard.normalize(question).strip()", "not question.strip()",
     ["backend.tests.test_api.ParseRequestTest"]),
    ("tanpa batas waktu socket", API,
     '"timeout": timeout})', '"timeout": None})',
     ["backend.tests.test_api.HttpTest.test_body_terpotong_tidak_menahan_server_selamanya"]),
]

env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
ok = True
for name, path, old, new, tests in MUTANTS:
    original = path.read_text(encoding="utf-8")
    assert old in original, name
    path.write_text(original.replace(old, new, 1), encoding="utf-8", newline="\n")
    try:
        proc = subprocess.run([sys.executable, "-m", "unittest", *tests], cwd=REPO, env=env,
                              capture_output=True, timeout=300)
        red = proc.returncode != 0
    except subprocess.TimeoutExpired:
        red = True  # tes menggantung = juga tertangkap
    finally:
        path.write_text(original, encoding="utf-8", newline="\n")
    ok &= red
    print("%-6s %s" % ("MERAH" if red else "LOLOS!", name))
sys.exit(0 if ok else 1)
