#!/usr/bin/env python3
"""Audit log append-only berantai hash (S6).

Setiap baris JSONL membawa `seq`, `prev_hash` (hash baris sebelumnya) dan
`hash` (SHA-256 isi baris itu sendiri tanpa field `hash`). Mengubah, menghapus,
atau menyisipkan baris di tengah membuat verify() gagal tepat di baris itu.

Batas yang perlu diketahui:
  - Memotong ekor log tidak terdeteksi dari isi file saja. Simpan `head()`
    di luar file (laporan harian, tiket) bila butuh jaminan itu.
  - Kunci hanya berlaku dalam satu proses. Satu file log = satu server.

Baris lama tanpa `hash` (format sebelum rantai) tetap diterima: baris pertama
yang berantai menunjuk ke SHA-256 teks mentah baris sebelumnya.

    python3 scripts/audit_chain.py --verify backend/logs/audit.jsonl
"""

import argparse
import hashlib
import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "0" * 64


def canonical(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_hash(record):
    return sha256_text(canonical({k: v for k, v in record.items() if k != "hash"}))


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AuditChain:
    _instances = {}
    _instances_lock = threading.Lock()

    @classmethod
    def for_path(cls, path):
        """Satu instance per file, supaya semua penulis di proses ini berbagi kunci."""
        key = str(Path(path).resolve())
        with cls._instances_lock:
            if key not in cls._instances:
                cls._instances[key] = cls(path)
            return cls._instances[key]

    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()

    def _lines(self):
        if not self.path.exists():
            return []
        return [l for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def _tail(self):
        """(seq, hash) baris terakhir; GENESIS untuk file kosong."""
        lines = self._lines()
        if not lines:
            return 0, GENESIS
        try:
            last = json.loads(lines[-1])
        except json.JSONDecodeError:
            last = None
        if isinstance(last, dict) and last.get("hash"):
            return int(last.get("seq") or len(lines)), last["hash"]
        return len(lines), sha256_text(lines[-1])

    def append(self, record):
        """Tulis satu baris. Mengembalikan record lengkap (dengan seq & hash)."""
        with self.lock:
            seq, head = self._tail()
            rec = dict(record)
            rec.setdefault("ts", now_iso())
            rec["seq"] = seq + 1
            rec["prev_hash"] = head
            rec["hash"] = record_hash(rec)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            return rec

    def records(self):
        out = []
        for line in self._lines():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def head(self):
        with self.lock:
            return self._tail()[1]

    def verify(self):
        """Periksa seluruh rantai. Mengembalikan dict ringkas untuk manusia & API."""
        with self.lock:
            lines = self._lines()
        prev_hash, chained, legacy = GENESIS, 0, 0
        for number, line in enumerate(lines, 1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                return {"ok": False, "line": number, "reason": "baris bukan JSON",
                        "checked": number - 1}
            if not isinstance(rec, dict) or "hash" not in rec:
                if chained:
                    return {"ok": False, "line": number,
                            "reason": "baris tanpa hash di tengah rantai", "checked": number - 1}
                legacy += 1
                prev_hash = sha256_text(line)
                continue
            if rec.get("prev_hash") != prev_hash:
                return {"ok": False, "line": number, "seq": rec.get("seq"),
                        "reason": "prev_hash tidak cocok (baris sebelumnya diubah/dihapus)",
                        "checked": number - 1}
            if record_hash(rec) != rec["hash"]:
                return {"ok": False, "line": number, "seq": rec.get("seq"),
                        "reason": "isi baris tidak cocok dengan hash-nya", "checked": number - 1}
            prev_hash = rec["hash"]
            chained += 1
        return {"ok": True, "checked": len(lines), "chained": chained, "legacy": legacy,
                "head": prev_hash}


def main():
    ap = argparse.ArgumentParser(description="Verifikasi audit log berantai SecuritySahabat.")
    ap.add_argument("--verify", required=True, help="Path file audit JSONL")
    args = ap.parse_args()
    result = AuditChain(args.verify).verify()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
