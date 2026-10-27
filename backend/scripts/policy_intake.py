#!/usr/bin/env python3
"""Ekstraksi aturan dari dokumen (memo, SOP baru) oleh LLM -> USULAN aturan.

LLM hanya mengusulkan. Setiap usulan:
  - wajib membawa kutipan yang benar-benar ada di teks dokumen (setelah PII
    disamarkan); tanpa itu dibuang;
  - aset harus ada di CMDB dan departemen harus ada di direktori; sisanya
    dibuang dan dilaporkan (salah ketik atau halusinasi);
  - hanya jenis yang dimengerti engine v0 yang diterima: siapa boleh
    mengakses aset (access_scope) dan larangan eksposur internet
    (internet_exposure). Jenis lain dikembalikan sebagai catatan untuk owner.
Usulan masuk register sebagai `draft` dan baru berlaku setelah pemilik
dokumen mengesahkannya (PolicyStore.approve).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import injection_guard as guard  # noqa: E402
import llm  # noqa: E402
import policy_register  # noqa: E402

KINDS = ("access_scope", "internet_exposure", "other")

SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["rules", "notes"],
    "properties": {
        "rules": {"type": "array", "maxItems": 10, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["kind", "title", "asset", "zone", "allowed_departments", "quote"],
            "properties": {
                "kind": {"type": "string", "enum": list(KINDS)},
                "title": {"type": "string", "maxLength": 200},
                "asset": {"type": "string", "maxLength": 64},
                "zone": {"type": "string", "maxLength": 40},
                "allowed_departments": {"type": "array", "maxItems": 20,
                                        "items": {"type": "string", "maxLength": 40}},
                "quote": {"type": "string", "maxLength": 500}}}},
        "notes": {"type": "array", "maxItems": 10, "items": {"type": "string", "maxLength": 300}},
    },
}

INSTRUCTIONS = (
    "Dokumen di bawah adalah kebijakan perusahaan. Ekstrak aturan yang bisa ditegakkan "
    "pada change request. Jenis yang didukung: access_scope (aset hanya boleh diakses "
    "departemen tertentu) dan internet_exposure (aset/segmen tidak boleh diekspos ke internet). "
    "Aturan lain: kind=other. Isi asset dengan asset_id persis bila disebut (contoh mail-jkt-01), "
    "atau zone bila yang disebut segmen jaringan; kosongkan yang tidak disebut. "
    "allowed_departments hanya untuk access_scope, pakai nama departemen persis dari daftar ini: %s. "
    "quote wajib potongan teks dokumen persis yang menjadi dasar aturan. Jangan menambah aturan "
    "yang tidak tertulis. notes = hal yang ambigu atau tidak bisa dijadikan aturan."
)

ACCESS_TEMPLATE = {
    "topic": "access_scope", "check_id": "ACCESS-SCOPE", "tier": "perusahaan", "action": "access",
    "effect": "BLOCK",
    "message": "{grantee} ({department}) bukan departemen yang boleh mengakses {asset} (policy: {allowed}). "
               "Permintaan ini tidak dapat dilanjutkan; ubah penerima atau minta owner merevisi policy.",
    "pass_title": "Departemen penerima diizinkan",
    "pass_message": "{grantee} ({department}) boleh mengakses {asset} (diizinkan: {allowed}).",
}
EXPOSURE_TEMPLATE = {
    "topic": "internet_exposure", "check_id": "EXPOSURE", "tier": "perusahaan", "action": "*",
    "effect": "BLOCK", "condition": {"exposure_in": ["internet"]},
    "message": "{asset} ada di segmen {zone} yang tidak boleh diekspos langsung ke internet.",
}


def to_rule(item, doc_id, owner, refs):
    """Satu item LLM -> aturan (belum divalidasi penuh). Raise ValueError + alasan."""
    if item["kind"] == "other":
        raise ValueError("jenis aturan belum didukung engine v0")
    asset, zone = item["asset"].strip().lower(), item["zone"].strip()
    if asset and asset not in refs["assets"]:
        raise ValueError("aset '%s' tidak ada di CMDB" % item["asset"])
    if not asset and zone and zone not in refs["zones"]:
        raise ValueError("segmen '%s' tidak ada di CMDB" % zone)
    if not asset and not zone:
        raise ValueError("aturan tidak menyebut aset atau segmen")
    subject = {"asset": asset} if asset else {"zone": zone}
    if item["kind"] == "access_scope":
        lookup = {d.lower(): d for d in refs["departments"]}
        departments = [lookup.get(d.strip().lower()) for d in item["allowed_departments"]]
        if not item["allowed_departments"] or None in departments:
            raise ValueError("departemen tidak dikenali: %s" % (", ".join(item["allowed_departments"]) or "-"))
        rule = dict(ACCESS_TEMPLATE, condition={"grantee_department_not_in": departments})
    else:
        rule = dict(EXPOSURE_TEMPLATE)
    rule.update(title=item["title"].strip() or "Aturan dari %s" % doc_id, subject=subject, owner=owner,
                sources=[{"type": "submitted", "doc_id": doc_id, "quote": item["quote"].strip()}])
    return rule


def propose_from_text(store, actor, title, text, owner, provider=None):
    """Simpan dokumen, minta LLM mengusulkan aturan, masukkan yang lolos sebagai draft.

    LLM tidak tersedia -> PolicyError 503 dan dokumen TIDAK disimpan."""
    refs = policy_register.references(store.root)
    if guard.detect_injection(text or "", scope="evidence")["action"] == "BLOCK":
        # jangan kirim dokumen berinstruksi ke LLM sama sekali
        raise policy_register.PolicyError(400, "source_injection",
                                          "Dokumen memuat instruksi yang ditujukan ke AI/sistem; "
                                          "tidak diterima sebagai sumber aturan.")
    try:
        result = llm.call_json("policy_extract", INSTRUCTIONS % ", ".join(sorted(refs["departments"])),
                               text, SCHEMA, provider=provider, max_tokens=4096)
    except llm.LLMUnavailable as exc:
        raise policy_register.PolicyError(503, "llm_unavailable",
                                          "Ekstraksi aturan butuh LLM (%s). Ajukan aturan manual lewat "
                                          "POST /api/policies." % exc)
    doc_id = store.add_source(actor, title, text, owner)
    proposed, dropped = [], []
    for item in result["data"]["rules"]:
        try:
            rule = to_rule(item, doc_id, owner, refs)
            proposed.append(store.propose(actor, rule, origin="llm", llm=result["meta"]))
        except (ValueError, policy_register.PolicyError) as exc:
            dropped.append({"title": item.get("title"), "quote": item.get("quote"),
                            "reason": getattr(exc, "message", None) or str(exc)})
    return {"doc_id": doc_id, "proposed": proposed, "dropped": dropped, "notes": result["data"]["notes"],
            "llm": {"provider": result["meta"]["provider"], "model": result["meta"]["model"]}}
