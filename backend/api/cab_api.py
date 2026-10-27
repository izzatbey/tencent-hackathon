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
from audit_chain import AuditChain  # noqa: E402
from cab_request import CHANNELS, CabError, CabStore, Clock  # noqa: E402

ID_RE = re.compile(r"^/api/requests/(CR-[0-9a-f]{10})(?:/([a-z]+))?$")
ACTIONS = ("update", "submit", "approve", "reject", "dispatch", "undo", "review", "cancel")
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
    return path in ("/api/intake", "/api/requests", "/api/audit/verify", "/api/demo/clock") \
        or path.startswith("/api/requests/")


def handle_get(path, query, audit_path):
    store = store_for(audit_path)
    if path == "/api/audit/verify":
        return store.chain.verify()
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
