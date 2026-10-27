#!/usr/bin/env python3
"""Rakit paket submission "exported WorkBuddy workflow + evidence of use" (handbook §7).

Jalankan:
    python tools/export_submission.py              -> dist/submission/SecuritySahabat-workbuddy-export.zip
    python tools/export_submission.py --out X.zip  -> lokasi lain
Repo harus bersih (semua sudah di-commit) supaya isi zip sama persis dengan satu
commit; --allow-dirty hanya untuk uji coba.

Isi zip dijelaskan di docs/submission/export-readme.md (menjadi README.md di
dalam zip). Paket skill dirakit ulang lewat tools/pack_skill.py setiap kali.
"""

import hashlib
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO / "dist" / "submission" / "SecuritySahabat-workbuddy-export.zip"

# (sumber di repo, tujuan di zip). Folder disalin rekursif.
LAYOUT = [
    ("docs/submission/export-readme.md", "README.md"),
    ("dist/security-sahabat.skill", "workflow/security-sahabat.skill"),
    (".codebuddy/skills/security-sahabat", "workflow/project-skill"),
    ("docs/test-results/workbuddy", "evidence/workbuddy-screenshots"),
    ("docs/workbuddy-memory", "evidence/workbuddy-agent-memory"),
    ("docs/submission/workbuddy-provenance.md", "evidence/workbuddy-provenance.md"),
    ("docs/test-results/README.md", "evidence/test-results/README.md"),
    ("docs/test-results/pracab.md", "evidence/test-results/pracab.md"),
    ("docs/test-results/pracab-demo.txt", "evidence/test-results/pracab-demo.txt"),
    ("docs/test-results/screenshots", "evidence/test-results/screenshots"),
    ("docs/submission/accountability-sheet.md", "submission/accountability-sheet.md"),
    ("docs/submission/project-description.md", "submission/project-description.md"),
    ("docs/submission/product-sharing.md", "submission/product-sharing.md"),
    ("docs/architecture-diagram.svg", "submission/architecture-diagram.svg"),
    ("docs/architecture.md", "submission/architecture.md"),
    ("docs/workbuddy.md", "submission/workbuddy.md"),
]


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True).stdout


def files_under(src):
    if src.is_file():
        yield src, ""
        return
    for p in sorted(src.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
            yield p, p.relative_to(src).as_posix()


def entries():
    for src, dest in LAYOUT:
        path = REPO / src
        if not path.exists():
            raise SystemExit("hilang: %s" % src)
        for p, rel in files_under(path):
            yield p, "%s/%s" % (dest, rel) if rel else dest
    for rel in git("ls-files", "-z").split("\0"):
        if rel and (REPO / rel).is_file():
            yield REPO / rel, "source/" + rel


def main(argv):
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else DEFAULT_OUT
    dirty = git("status", "--porcelain").strip()
    if dirty and "--allow-dirty" not in argv:
        sys.stderr.write("Repo belum bersih; commit dulu supaya paket sama dengan satu commit:\n%s\n" % dirty)
        return 2
    subprocess.run([sys.executable, str(REPO / "tools" / "pack_skill.py")], cwd=REPO, check=True,
                   capture_output=True)

    commit = git("rev-parse", "HEAD").strip()
    version = "commit %s%s\ndibuat %s\n" % (commit, " (+ perubahan belum di-commit)" if dirty else "",
                                           datetime.now(timezone.utc).isoformat(timespec="seconds"))
    out.parent.mkdir(parents=True, exist_ok=True)
    sums = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in entries():
            data = src.read_bytes()
            z.writestr(arc, data)
            sums.append("%s  %s" % (hashlib.sha256(data).hexdigest(), arc))
        z.writestr("VERSION.txt", version)
        z.writestr("SHA256SUMS.txt", "\n".join(sums) + "\n")
    print("%s  files=%d  size=%d  commit=%s%s" % (out, len(sums) + 2, out.stat().st_size, commit[:10],
                                                  " DIRTY" if dirty else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
