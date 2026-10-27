#!/usr/bin/env python3
"""Project skill WorkBuddy (.codebuddy/skills/security-sahabat/) harus sama dengan sumbernya.

Folder itu di-commit supaya WorkBuddy langsung mendeteksi skill saat repo dibuka.
Kalau tes ini merah: jalankan `python tools/pack_skill.py --project` lalu commit.
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import pack_skill  # noqa: E402

ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")


class ProjectSkillTest(unittest.TestCase):

    def test_isi_project_skill_sama_persis_dengan_sumber(self):
        expected = {arc: src.read_bytes() for src, arc in pack_skill.entries()}
        installed = {p.relative_to(pack_skill.PROJECT_SKILL).as_posix(): p.read_bytes()
                     for p in pack_skill.PROJECT_SKILL.rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts}
        self.assertEqual(sorted(installed), sorted(expected), "daftar berkas beda")
        stale = [arc for arc in expected if installed.get(arc) != expected[arc]]
        self.assertEqual(stale, [], "berkas basi, jalankan tools/pack_skill.py --project")

    def test_paket_tidak_memuat_sumber_restricted_asli(self):
        self.assertFalse(any("knowledge-base/source" in arc or arc.startswith("source/")
                             for _, arc in pack_skill.entries()))

    def run_skill(self, question):
        script = pack_skill.PROJECT_SKILL / "scripts" / "search_kb.py"
        proc = subprocess.run([sys.executable, str(script), "-q", question, "--json"],
                              capture_output=True, env=ENV, timeout=60)
        return json.loads(proc.stdout.decode("utf-8"))

    def test_skill_terpasang_bisa_dijalankan_dari_foldernya_sendiri(self):
        result = self.run_skill("Saya Andini, IT Admin. Boleh buka port 22 dari internet ke db-hr-jkt-01?")
        self.assertEqual(result["status"], "OK")
        self.assertIn("CTRL-09", [h["doc_id"] for h in result["hits"]])
        self.assertIn(".codebuddy", result["kb_root"])

    def test_skill_terpasang_tidak_membocorkan_garuda(self):
        real = self.run_skill("Saya Sari, HR Staff. Who owns Project Garuda?")
        fake = self.run_skill("Saya Sari, HR Staff. Who owns Project Falcon?")
        strip = lambda r, n: json.dumps(r, sort_keys=True).replace(n, "<P>")  # noqa: E731
        self.assertEqual(strip(real, "Garuda"), strip(fake, "Falcon"))


if __name__ == "__main__":
    unittest.main()
