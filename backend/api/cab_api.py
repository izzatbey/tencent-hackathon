"""Endpoint Pra-CAB (dipanggil dari server.py). Persona dikirim sebagai `user`
(nama persis di permissions.csv); API demo belum punya login.

    POST /api/intake                     {user, text, channel}   teks bebas -> draft field + pertanyaan
    POST /api/requests                   {user, fields, intake_id?}
    GET  /api/requests?user=             daftar yang boleh dilihat persona
    GET  /api/requests/{id}?user=
    GET  /api/requests/{id}/audit?user=  baris audit mentah (dengan hash)
    POST /api/requests/{id}/{aksi}       {user, ...}
         aksi: update {fields} · submit · approve {slot, meeting?, note?} · reject {reason}
               dispatch · undo · review {note?} · cancel {reason?}
    GET  /api/audit/verify               status rantai hash audit log
    POST /api/demo/clock                 {now: ISO | null}  hanya dengan server --demo

  Policy register:
    GET  /api/policies?user=[&status=]   semua aturan (seed + yang diajukan lewat aplikasi)
    GET  /api/policies/{id}?user=
    POST /api/policies                   {user, rule, source?: {title, text, owner}}   usulan manual
    POST /api/policies/extract           {user, title, text, owner}   LLM mengusulkan dari dokumen
    POST /api/policies/{id}/approve      {user}            hanya owner dokumen sumber, bukan pengusul
    POST /api/policies/{id}/reject       {user, reason}
    POST /api/policies/{id}/retire       {user, reason}

Permintaan yang tidak ada dan yang tidak boleh dilihat dijawab 404 yang sama.
"""

import re
import sys
from pathlib import Path
from urllib.parse import parse_qs

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND / "scripts"))
import cab_intake  # noqa: E402
import cab_rules  # noqa: E402
import kb_facts  # noqa: E402
import policy_intake  # noqa: E402
import policy_register  # noqa: E402
from audit_chain import AuditChain  # noqa: E402
from cab_request import CHANNELS, CabError, CabStore, Clock  # noqa: E402

ID_RE = re.compile(r"^/api/requests/(CR-[0-9a-f]{10})(?:/([a-z]+))?$")
POLICY_RE = re.compile(r"^/api/policies/(POL-[0-9a-z]{4,12})(?:/([a-z]+))?$")
ACTIONS = ("update", "submit", "approve", "reject", "dispatch", "undo", "review", "cancel")
POLICY_ACTIONS = ("approve", "reject", "retire")
POLICY_STATUSES = ("draft", "active", "superseded", "retired", "rejected")
MAX_TEXT = 4000

CLOCK = Clock()
_stores = {}


def store_for(audit_path):
    """Satu store per file audit (tes memakai file sementara per kasus)."""
    key = str(Path(audit_path).resolve())
    if key not in _stores:
        _stores[key] = CabStore(AuditChain.for_path(audit_path), clock=CLOCK)
    return _stores[key]


# --------------------------------------------------------------------------
# DTO
# --------------------------------------------------------------------------
def approvals_view(req):
    pre = req["precheck"] or {}
    rejected_by = (req["rejection"] or {}).get("by")
    out = []
    for s in pre.get("approvals", []):
        got = req["approvals"].get(s["slot"])
        status = "approved" if got else ("rejected" if rejected_by == s["assignee"] else "pending")
        out.append({"slot": s["slot"], "label": s["label"], "assignee": s["assignee"],
                    "kind": s["kind"], "mode": s["mode"], "citations": s["citations"],
                    "reassigned_from": s.get("reassigned_from"), "status": status,
                    "by": got and got["by"], "at": got and got["at"],
                    "meeting": got and got["meeting"], "note": got and got["note"]})
    return out


def view(store, req, actor):
    return {
        "id": req["id"], "state": req["state"], "fields": req["fields"],
        "requester": req["requester"], "created_at": req["created_at"],
        "pii_masked": req["pii_masked"], "precheck": req["precheck"],
        "approvals": approvals_view(req), "rejection": req["rejection"],
        "dispatch": req["dispatch"], "undo": req["undo"], "review": req["review"],
        "allowed_actions": store.allowed_actions(actor, req), "history": req["history"],
    }


def summary(store, req, actor):
    pre = req["precheck"] or {}
    return {"id": req["id"], "state": req["state"], "title": req["fields"].get("title"),
            "type": req["fields"].get("type"), "assets": req["fields"].get("assets"),
            "requester": req["requester"], "created_at": req["created_at"],
            "risk": (pre.get("risk") or {}).get("level"), "outcome": pre.get("outcome"),
            "allowed_actions": store.allowed_actions(actor, req)}


# --------------------------------------------------------------------------
# routing
# --------------------------------------------------------------------------
def _text(data, key, required=False, limit=MAX_TEXT):
    value = data.get(key)
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > limit:
        raise CabError(400, "invalid_%s" % key, "Field %s harus teks maksimal %d karakter." % (key, limit))
    return value


def handles(path):
    return path in ("/api/intake", "/api/requests", "/api/audit/verify", "/api/demo/clock",
                    "/api/policies", "/api/policies/extract") \
        or path.startswith("/api/requests/") or path.startswith("/api/policies/")


# --------------------------------------------------------------------------
# policy register
# --------------------------------------------------------------------------
POLICY_VIEW = ("id", "title", "topic", "check_id", "tier", "subject", "action", "condition", "effect",
               "approver", "approver_label", "approver_sources", "message", "pass_title", "pass_message",
               "emergency_effect", "emergency_message", "basis", "sources",
               "owner", "effective_date", "supersedes", "status", "origin", "proposed_by", "proposed_at",
               "approved_by", "approved_at", "superseded_by", "rejected_by", "retired_by", "reason", "history")


def policy_view(policies, rule, actor):
    out = {k: rule.get(k) for k in POLICY_VIEW}
    docs = {s.get("doc_id") for s in rule.get("sources", []) if s.get("type") == "submitted"}
    out["source_documents"] = [{"doc_id": d, "title": policies.sources[d]["title"],
                                "owner": policies.sources[d]["owner"], "sha256": policies.sources[d]["sha256"],
                                "added_by": policies.sources[d]["by"], "added_at": policies.sources[d]["at"]}
                               for d in sorted(docs) if d in policies.sources]
    out["allowed_actions"] = policies.allowed_actions(actor, rule)
    return out


def handle_policies_get(store, path, query):
    params = parse_qs(query)
    actor = store.actor((params.get("user") or [None])[0])
    policies = store.policies
    if path == "/api/policies":
        status = (params.get("status") or [None])[0]
        if status is not None and status not in POLICY_STATUSES:
            raise CabError(400, "invalid_status", "status salah satu dari %s." % ", ".join(POLICY_STATUSES))
        rules = [r for r in policies.rules.values() if status is None or r["status"] == status]
        return {"policies": [policy_view(policies, r, actor) for r in sorted(rules, key=lambda r: r["id"])]}
    m = POLICY_RE.match(path)
    if not m or m.group(2) is not None:
        raise CabError(404, "not_found", "Tidak ditemukan.")
    return policy_view(policies, policies.get(m.group(1)), actor)


def handle_policies_post(store, path, data, actor):
    policies = store.policies
    if path == "/api/policies":
        source = data.get("source")
        rule = data.get("rule")
        if source is not None:
            if not isinstance(source, dict) or not isinstance(rule, dict):
                raise CabError(400, "invalid_source", "source harus objek {title, text, owner}.")
            # validasi bentuk dulu supaya aturan rusak tidak meninggalkan dokumen yatim di log
            policy_register.validate_rule(rule, policy_register.references(policies.root))
            # source baru dibuat; kutipan bertipe submitted tanpa doc_id menunjuk ke sana
            doc_id = policies.add_source(actor, source.get("title"), source.get("text"), source.get("owner"))
            rule = dict(rule, sources=[dict(s, doc_id=doc_id) if isinstance(s, dict) and s.get("type") == "submitted"
                                       and not s.get("doc_id") else s for s in rule.get("sources") or []])
        return policy_view(policies, policies.propose(actor, rule), actor)
    if path == "/api/policies/extract":
        result = policy_intake.propose_from_text(policies, actor, _text(data, "title", required=True, limit=200),
                                                 _text(data, "text", required=True, limit=20000),
                                                 data.get("owner"))
        return dict(result, proposed=[policy_view(policies, r, actor) for r in result["proposed"]])
    m = POLICY_RE.match(path)
    if not m or m.group(2) not in POLICY_ACTIONS:
        raise CabError(404, "not_found", "Tidak ditemukan.")
    pid, action = m.groups()
    if action == "approve":
        rule = policies.approve(actor, pid)
    else:
        rule = getattr(policies, action)(actor, pid, _text(data, "reason", required=True, limit=1000))
    return policy_view(policies, rule, actor)


def handle_get(path, query, audit_path):
    store = store_for(audit_path)
    if path == "/api/audit/verify":
        return store.chain.verify()
    if path == "/api/policies" or path.startswith("/api/policies/"):
        return handle_policies_get(store, path, query)
    user = (parse_qs(query).get("user") or [None])[0]
    if path == "/api/requests":
        actor = store.actor(user)
        return {"requests": [summary(store, r, actor) for r in store.list_for(actor)]}
    m = ID_RE.match(path)
    if not m or m.group(2) not in (None, "audit"):
        raise CabError(404, "not_found", "Tidak ditemukan.")
    actor = store.actor(user)
    if m.group(2) == "audit":
        return {"records": store.records_for(actor, m.group(1))}
    return view(store, store._get(m.group(1), actor), actor)


def handle_post(path, data, audit_path, demo=False):
    store = store_for(audit_path)
    if path == "/api/demo/clock":
        if not demo:
            raise CabError(404, "not_found", "Tidak ditemukan.")
        now = data.get("now")
        fixed = cab_rules.parse_time(now) if now else None
        if now and fixed is None:
            raise CabError(400, "invalid_now", "now harus ISO-8601 dengan zona waktu.")
        CLOCK.set(fixed)
        return {"now": CLOCK.now().isoformat(timespec="seconds"), "fixed": CLOCK.fixed is not None}

    actor = store.actor(data.get("user"))
    if path == "/api/policies" or path.startswith("/api/policies/"):
        return handle_policies_post(store, path, data, actor)
    if path == "/api/intake":
        channel = data.get("channel") or "chat"
        if channel not in CHANNELS:
            raise CabError(400, "invalid_channel", "channel salah satu dari %s." % ", ".join(CHANNELS))
        text = _text(data, "text", required=True)
        today = CLOCK.now().astimezone(kb_facts.tz("WIB")).date().isoformat()
        result = cab_intake.draft_from_text(text, channel=channel, today=today)
        intake_id = store.record_intake(actor, result)
        return {"intake_id": intake_id, "fields": result["fields"], "questions": result["questions"],
                "dropped": result["dropped"], "warnings": result["warnings"],
                "llm": {"provider": result["llm"]["provider"], "model": result["llm"]["model"]}
                if result.get("llm") else None}
    if path == "/api/requests":
        intake_id = data.get("intake_id")
        if intake_id is not None and not isinstance(intake_id, str):
            raise CabError(400, "invalid_intake", "intake_id tidak dikenal.")
        req = store.create(actor, data.get("fields"), intake_id=intake_id)
        return view(store, req, actor)

    m = ID_RE.match(path)
    if not m or m.group(2) not in ACTIONS:
        raise CabError(404, "not_found", "Tidak ditemukan.")
    cr_id, action = m.groups()
    if action == "update":
        req = store.update(actor, cr_id, data.get("fields"))
    elif action == "approve":
        req = store.approve(actor, cr_id, _text(data, "slot", required=True, limit=80),
                            meeting=_text(data, "meeting", limit=40), note=_text(data, "note", limit=1000))
    elif action == "reject":
        req = store.reject(actor, cr_id, _text(data, "reason", required=True, limit=1000))
    elif action in ("review", "cancel"):
        key = "note" if action == "review" else "reason"
        req = getattr(store, action)(actor, cr_id, _text(data, key, limit=1000))
    else:
        req = getattr(store, action)(actor, cr_id)
    return view(store, req, actor)
