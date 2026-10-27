#!/usr/bin/env python3
"""Intake Pra-CAB: teks bebas (chat, email, tiket, transkrip voice) -> draft field CR.

Satu-satunya tugas LLM di jalur ini: menyalin informasi dari teks ke field.
Pengaman setelah LLM menjawab:
  - setiap field teks wajib punya `evidence` yang benar-benar ada di teks
    (setelah PII disamarkan); field tanpa bukti dibuang dan dilaporkan;
  - asset_id harus ada di CMDB, sisanya jadi pertanyaan klarifikasi;
  - jadwal tanpa zona waktu dibuang (WIB/WITA/WIT tidak boleh ditebak).
Hasilnya hanya DRAFT. Pemohon memeriksa dan mengirim field-nya sendiri lewat
POST /api/requests; risiko dan approver tetap diputuskan cab_rules.

LLM tidak aktif / gagal -> fallback: seluruh teks jadi `description`, field
lain kosong, dan pemohon diminta melengkapi.
"""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cab_rules  # noqa: E402
import injection_guard as guard  # noqa: E402
import kb_facts  # noqa: E402
import llm  # noqa: E402

MAX_TEXT = 4000
TEXT_KEYS = ("title", "description", "reason", "impact", "implementation_plan", "rollback_plan")

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": list(TEXT_KEYS) + ["assets", "change_kind", "exposure", "ports", "window_start",
                                   "window_end", "emergency", "evidence", "questions"],
    "properties": dict(
        {k: {"type": "string", "maxLength": 2000} for k in TEXT_KEYS},
        assets={"type": "array", "maxItems": 20, "items": {"type": "string", "maxLength": 64}},
        change_kind={"type": "string", "enum": list(cab_rules.CHANGE_KINDS)},
        exposure={"type": "string", "enum": list(cab_rules.EXPOSURES)},
        ports={"type": "array", "maxItems": 20, "items": {"type": "integer"}},
        window_start={"type": "string", "maxLength": 40},
        window_end={"type": "string", "maxLength": 40},
        emergency={"type": "boolean"},
        evidence={"type": "array", "maxItems": 20, "items": {
            "type": "object", "additionalProperties": False, "required": ["field", "quote"],
            "properties": {"field": {"type": "string", "maxLength": 40},
                           "quote": {"type": "string", "maxLength": 500}}}},
        questions={"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 300}},
    ),
}

INSTRUCTIONS = (
    "Ubah permintaan perubahan IT di bawah menjadi field change request. Isi hanya yang "
    "tertulis; kosongkan field yang tidak disebut (string kosong, array kosong). "
    "assets = asset_id persis seperti di teks (contoh fw-edge-mks-01). window_start/"
    "window_end = ISO-8601 dengan offset zona (+07:00 WIB, +08:00 WITA, +09:00 WIT) hanya bila "
    "tanggal, jam, dan zonanya jelas; kalau tidak, kosongkan dan tanyakan di questions. "
    "Untuk setiap field teks yang kamu isi, tambahkan evidence {field, quote} dengan quote "
    "berupa potongan teks asli persis. questions = pertanyaan klarifikasi singkat bila ada "
    "yang ambigu. Tanggal hari ini: %s."
)


def _fallback(masked, reason):
    return {"fields": {"description": masked[:MAX_TEXT]}, "dropped": [], "llm": None,
            "questions": ["Lengkapi aset, alasan, dampak, rencana, rollback, dan jadwal."],
            "warnings": ["Penafsir otomatis tidak dipakai (%s); teks disalin apa adanya." % reason]}


def draft_from_text(text, channel="chat", today=None, provider=None, root=None):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("teks kosong")
    text = text.strip()[:MAX_TEXT]
    warnings = []
    if guard.detect_injection(text, scope="query")["action"] in ("BLOCK", "WARN"):
        warnings.append("Teks memuat kalimat yang ditujukan ke sistem/AI. Kalimat itu diperlakukan "
                        "sebagai data dan tidak dijalankan.")
    try:
        result = llm.call_json("cab_intake", INSTRUCTIONS % (today or "tidak diketahui"),
                               text, SCHEMA, provider=provider, max_tokens=4096)
    except llm.LLMUnavailable as exc:
        masked, _ = llm.pii.mask_pii(text, types=llm.PII_TYPES)
        out = _fallback(masked, str(exc))
        out["warnings"] = warnings + out["warnings"]
        out.update(channel=channel, input_sha256=hashlib.sha256(masked.encode("utf-8")).hexdigest())
        return out

    data, masked = result["data"], result["masked_text"]
    plain = " ".join(masked.split())
    supported = {e["field"] for e in data["evidence"]
                 if e["quote"].strip() and " ".join(e["quote"].split()) in plain}
    fields, dropped = {}, []
    for key in TEXT_KEYS:
        value = data[key].strip()
        if not value:
            continue
        if key in supported:
            fields[key] = value
        else:
            dropped.append({"field": key, "reason": "tidak ada kutipan pendukung di teks asli"})

    cmdb = kb_facts.load_cmdb(root)
    questions = list(data["questions"])
    known = [a.strip().lower() for a in data["assets"] if a.strip().lower() in cmdb]
    unknown = [a for a in data["assets"] if a.strip().lower() not in cmdb]
    if known:
        fields["assets"] = list(dict.fromkeys(known))
    if unknown:
        dropped.append({"field": "assets", "reason": "tidak ada di CMDB: %s" % ", ".join(unknown)})
        questions.append("Aset %s tidak ada di CMDB. asset_id mana yang dimaksud?" % ", ".join(unknown))

    start, end = cab_rules.parse_time(data["window_start"]), cab_rules.parse_time(data["window_end"])
    if start and end and start < end:
        fields["window"] = {"start": start.isoformat(), "end": end.isoformat()}
    elif data["window_start"] or data["window_end"]:
        dropped.append({"field": "window", "reason": "jadwal tanpa zona waktu atau tidak valid"})
        questions.append("Jadwalnya jam berapa, dan dalam WIB, WITA, atau WIT?")

    fields.update(change_kind=data["change_kind"], exposure=data["exposure"],
                  ports=[p for p in data["ports"] if 0 < p < 65536], emergency=data["emergency"],
                  channel=channel)
    return {"fields": fields, "dropped": dropped, "questions": questions[:5],
            "warnings": warnings, "llm": result["meta"], "channel": channel,
            "input_sha256": result["meta"]["input_sha256"]}
