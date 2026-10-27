#!/usr/bin/env python3
"""Tes paket submission (tools/export_submission.py): isi wajib ada dan checksum cocok.

    python -m unittest backend.tests.test_export
"""

import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "export_submission.py"


class ExportTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="export-"))
        cls.zip_path = cls.tmp / "export.zip"
        proc = subprocess.run([sys.executable, str(SCRIPT), "--allow-dirty", "--out", str(cls.zip_path)],
                              cwd=ROOT, capture_output=True, text=True)
        if proc.returncode:
            raise AssertionError(proc.stderr)
        cls.zip = zipfile.ZipFile(cls.zip_path)
        cls.names = set(cls.zip.namelist())

    @classmethod
    def tearDownClass(cls):
        cls.zip.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_isi_wajib_ada(self):
        for name in ("README.md", "VERSION.txt", "SHA256SUMS.txt", "workflow/security-sahabat.skill",
                     "workflow/project-skill/SKILL.md", "evidence/workbuddy-provenance.md",
                     "evidence/workbuddy-screenshots/skill-creator-task-47-artifacts.jpg",
                     "evidence/test-results/pracab.md", "submission/accountability-sheet.md",
                     "submission/product-sharing.md",
                     "submission/architecture-diagram.svg", "source/backend/scripts/search_kb.py",
                     "source/frontend/package.json"):
            with self.subTest(name=name):
                self.assertIn(name, self.names)

    def test_checksum_cocok_dengan_isi(self):
        lines = self.zip.read("SHA256SUMS.txt").decode("utf-8").split("\n")
        sums = dict(reversed(line.split("  ", 1)) for line in lines if line)
        self.assertEqual(set(sums), self.names - {"SHA256SUMS.txt", "VERSION.txt"})
        for name, digest in sums.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256(self.zip.read(name)).hexdigest(), digest)

    def test_paket_skill_di_dalamnya_bisa_dibuka(self):
        with zipfile.ZipFile(self.zip.open("workflow/security-sahabat.skill")) as skill:
            self.assertIn("security-sahabat/SKILL.md", skill.namelist())

    def test_tanpa_file_yang_diabaikan_git(self):
        self.assertFalse([n for n in self.names if "/logs/" in n or "node_modules/" in n or n.endswith(".pyc")])


if __name__ == "__main__":
    unittest.main()
