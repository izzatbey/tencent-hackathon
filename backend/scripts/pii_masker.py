#!/usr/bin/env python3
"""Penyamaran PII untuk SecuritySahabat.

Dipakai pada **query** sebelum retrieval, supaya data pribadi tidak ikut masuk
ke pencarian, log, maupun jawaban. Penyamaran evidence bersifat opsional
(`mask_pii_in_evidence` di config.json) karena aturan kutipan mewajibkan
kutipan verbatim — menyunting angka di dalam kutipan bisa merusak bukti
(topologi, port, IP asset).

Catatan penting: `mask_log` **hanya mencatat tipe dan bentuk tersamarkan**.
Nilai asli tidak pernah disimpan — kalau disimpan, log/JSON berubah jadi
salinan data pribadi, padahal tujuannya justru menghilangkannya.

Uji langsung:
    python3 scripts/pii_masker.py --text "NIK saya 3175091234567890, hubungi +6281234567890"
"""

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def mask_email(email: str) -> str:
    """budi.santoso@email.com -> [EMAIL: b***********@email.com]"""
    local, _, domain = email.partition("@")
    masked_local = local[0] + "*" * (len(local) - 1) if len(local) > 1 else "*"
    return f"[EMAIL: {masked_local}@{domain}]"


# (regex, tipe, fungsi penyamar). Urutan penting: NIK/telepon sebelum IP,
# supaya angka panjang tidak dipotong dulu oleh pola yang lebih umum.
# NIK dan telepon sering ditulis berkelompok ("3175 0912 3456 7890",
# "0812-3456-7890", "+62 812 3456 7890"), jadi pemisah spasi/titik/strip ikut cocok.
PII_PATTERNS = [
    (r"\b\d{4}([ .-]?)\d{4}\1\d{4}\1\d{4}\b", "NIK", lambda m: f"[NIK: ****{m.group(0)[-4:]}]"),
    (r"(?:\+62|\b62|\b0)[ .-]?8(?:[ .-]?\d){8,11}(?!\d)", "PHONE",
     lambda m: f"[PHONE: ****{m.group(0)[-4:]}]"),
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "EMAIL",
     lambda m: mask_email(m.group(0))),
    (r"\bNLP-\d{3}\b", "EMP-ID", lambda m: "[EMP-ID: NLP-***]"),
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "IP",
     lambda m: f"[IP: {m.group(0).rsplit('.', 1)[0]}.***]"),
]


def mask_pii(text: str, types=None) -> tuple:
    """Samarkan PII. Mengembalikan (teks_tersamarkan, log_penyamaran).

    `types` opsional: himpunan tipe yang disamarkan saja (mis. {"NIK", "PHONE"}).
    Log berisi {"type", "masked"} saja — tanpa nilai asli.
    """
    masked = text or ""
    mask_log = []

    for pattern, pii_type, mask_func in PII_PATTERNS:
        if types and pii_type not in types:
            continue
        for match in list(re.finditer(pattern, masked)):
            original = match.group(0)
            replacement = mask_func(match)
            masked = masked.replace(original, replacement, 1)
            mask_log.append({"type": pii_type, "masked": replacement})

    return masked, mask_log


def summarize(log) -> str:
    """Ringkas log: "NIK x1, PHONE x2"."""
    counts = {}
    for entry in log:
        counts[entry["type"]] = counts.get(entry["type"], 0) + 1
    return ", ".join("%s x%d" % (t, c) for t, c in sorted(counts.items()))


def enabled(scope="query") -> bool:
    """Apakah penyamaran aktif untuk scope ini (aturan dari config.json)."""
    cfg = SKILL_DIR / "config.json"
    if not cfg.exists():
        return scope == "query"
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return scope == "query"
    if scope == "evidence":
        return bool(data.get("mask_pii_in_evidence", False))
    return bool(data.get("mask_pii", True))


def main():
    ap = argparse.ArgumentParser(description="Uji penyamaran PII SecuritySahabat.")
    ap.add_argument("--text", "-t", help="Teks yang akan disamarkan")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    masked, mask_log = mask_pii(args.text or "")
    if args.json:
        print(json.dumps({"masked_text": masked, "mask_log": mask_log},
                         indent=2, ensure_ascii=False))
    else:
        print(masked)
        if mask_log:
            print("masked: %s" % summarize(mask_log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
