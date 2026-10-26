#!/usr/bin/env python3
"""Rakit paket Claude skill dari layout repo.

Jalankan:
    python tools/pack_skill.py            -> dist/security-sahabat.skill

Isi paket (layout yang diharapkan SKILL.md):
    security-sahabat/SKILL.md, references/   <- skill/
    security-sahabat/config.json, scripts/   <- backend/ (+ tests/verify_matrix.py)
    security-sahabat/kb/                     <- knowledge-base/kb/
knowledge-base/source/ sengaja TIDAK ikut (berisi teks restricted asli).
"""

import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NAME = "security-sahabat"

SOURCES = [
    (REPO / "skill", ""),
    (REPO / "backend" / "config.json", "config.json"),
    (REPO / "backend" / "scripts", "scripts"),
    (REPO / "backend" / "tests" / "verify_matrix.py", "scripts/verify_matrix.py"),
    (REPO / "knowledge-base" / "kb", "kb"),
]


def entries():
    for src, dest in SOURCES:
        if src.is_file():
            yield src, dest
            continue
        for p in sorted(src.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
                rel = p.relative_to(src).as_posix()
                yield p, "%s/%s" % (dest, rel) if dest else rel


def main():
    out = REPO / "dist" / ("%s.skill" % NAME)
    out.parent.mkdir(exist_ok=True)
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in entries():
            z.write(src, "%s/%s" % (NAME, arc))
            n += 1
    print("%s  files=%d  size=%d" % (out, n, out.stat().st_size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
