#!/usr/bin/env python3
"""Fakta terstruktur untuk Pra-CAB: CMDB, direktori staf, dan kutipan terverifikasi.

Setiap aturan Pra-CAB mengutip sumbernya lewat cite(). Kutipan hanya sah bila
teksnya benar-benar ada di dokumen KB (dibandingkan setelah format markdown
`**`/`*`/`` ` `` dan spasi dinormalkan). Kutipan yang tidak ditemukan me-raise
CitationError: aturan yang kehilangan sumbernya harus ketahuan di tes, bukan
diam-diam tampil tanpa bukti.

Sumber:
  kb/cmdb.csv        salinan knowledge-base/source/cmdb.csv
  kb/directory.csv   contacts.csv tanpa email & telepon
  kb/**.md           dokumen KB (lewat search_kb.load_documents)
  source/chat_exports.jsonl  hanya untuk mengutip memo yang belum masuk KB
"""

import csv
import json
import re
import sys
from datetime import timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import search_kb  # noqa: E402

# Indonesia tidak memakai DST, jadi offset tetap cukup (zoneinfo di Windows
# butuh paket tzdata, yang ingin kita hindari).
TZ_OFFSET = {"WIB": 7, "WITA": 8, "WIT": 9}
SITE_TZ = {"Jakarta": "WIB", "Makassar": "WITA", "Jayapura": "WIT"}


class CitationError(Exception):
    pass


def tz(name):
    return timezone(timedelta(hours=TZ_OFFSET[name]), name)


def site_tz(site):
    return tz(SITE_TZ.get(site, "WIB"))


def kb_root(root=None):
    return search_kb.resolve_kb_root(root)


def _read_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_cmdb(root=None):
    """{asset_id: row} dari kb/cmdb.csv."""
    return {r["asset_id"].strip(): {k: (v or "").strip() for k, v in r.items()}
            for r in _read_csv(kb_root(root) / "cmdb.csv") if r.get("asset_id")}


def load_directory(root=None):
    return [{k: (v or "").strip() for k, v in r.items()}
            for r in _read_csv(kb_root(root) / "directory.csv") if r.get("name")]


def owner_name(owner):
    """'Ragil Wibowo (Ops Manager Mks)' -> 'Ragil Wibowo'."""
    return str(owner or "").split("(", 1)[0].strip()


# --------------------------------------------------------------------------
# kutipan
# --------------------------------------------------------------------------
def _plain(text):
    text = re.sub(r"[*`]", "", str(text or ""))
    return " ".join(text.split())


def _documents(root):
    return {str(d["meta"].get("doc_id")): d for d in search_kb.load_documents(kb_root(root))}


def cite(doc_id, needle, root=None, docs=None):
    """Kutipan {doc_id, title, section, quote, effective_date, owner} bila
    `needle` ada di dokumen `doc_id`. Dokumen restricted tidak pernah dikutip."""
    docs = docs if docs is not None else _documents(root)
    doc = docs.get(doc_id)
    if doc is None:
        raise CitationError("dokumen %s tidak ada di KB" % doc_id)
    meta = doc["meta"]
    if search_kb.is_restricted(meta):
        raise CitationError("dokumen %s restricted, tidak boleh dikutip" % doc_id)
    want = _plain(needle)
    for heading, text in doc["sections"]:
        if want and want in _plain(text):
            return {"doc_id": doc_id, "title": meta.get("title"), "section": heading,
                    "quote": want, "effective_date": meta.get("effective_date"),
                    "owner": meta.get("owner")}
    raise CitationError("kutipan tidak ditemukan di %s: %r" % (doc_id, needle[:60]))


def cite_cmdb(asset_id, field="notes", needle=None, cmdb=None):
    """Kutip satu sel CMDB. Tanpa `needle`, seluruh isi sel dikutip."""
    cmdb = cmdb if cmdb is not None else load_cmdb()
    row = cmdb.get(asset_id)
    if row is None:
        raise CitationError("aset %s tidak ada di CMDB" % asset_id)
    value = row.get(field, "")
    quote = needle or value
    if not quote or quote not in value:
        raise CitationError("kutipan CMDB %s.%s tidak ditemukan" % (asset_id, field))
    return {"doc_id": "CMDB", "title": "CMDB · %s" % row.get("name"), "section": "%s.%s" % (asset_id, field),
            "quote": quote, "effective_date": None, "owner": None}


def cite_chat(ts, needle, root=None):
    """Kutip pesan chat export (memo yang belum dipecah ke KB). Hanya pesan
    dengan timestamp persis `ts` yang dibaca; pesan lain tidak disentuh."""
    path = kb_root(root).parent / "source" / "chat_exports.jsonl"
    if not path.exists():
        raise CitationError("chat_exports.jsonl tidak tersedia")
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("ts") != ts:
            continue
        if needle not in msg.get("message", ""):
            break
        return {"doc_id": "CHAT %s" % ts[:16], "title": "%s · %s" % (msg.get("chat"), msg.get("sender")),
                "section": ts, "quote": needle, "effective_date": ts[:10], "owner": msg.get("sender")}
    raise CitationError("pesan chat %s tidak ditemukan" % ts)
