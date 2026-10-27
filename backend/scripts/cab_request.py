#!/usr/bin/env python3
"""Change request Pra-CAB: model, state machine, dan penyimpanan di audit log.

State hanya berubah lewat event, dan setiap event ditulis ke audit chain lebih
dulu. State di memori adalah hasil memutar ulang event itu, jadi riwayat yang
ditampilkan selalu cocok dengan state yang dilayani API, dan server yang
di-restart memulihkan semua permintaan dari log.

    draft ─submit─▶ pending_approval ─semua slot disetujui─▶ approved ─dispatch─▶ dispatched
      ▲     ├─▶ returned (NEEDS_INFO / NEEDS_REVISION)  └─reject─▶ rejected          ├─undo ≤60 dtk─▶ undone
      │     └─▶ blocked  (BLOCK)                                                     └─(emergency) retro_review ─review─▶ closed
      └── update dari draft/returned/blocked/pending_approval/approved: persetujuan lama gugur
    cancel: oleh pemohon, sebelum dispatch

Tidak ada eksekusi sungguhan. Dispatch hanya memanggil mock tool (undangan
kalender, tiket change register, tugas notifikasi) dan mencatat "would have sent".
Upaya yang ditolak (mis. dispatch sebelum disetujui) ikut dicatat sebagai
event `denied`.
"""

import hashlib
import re
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cab_rules  # noqa: E402
import kb_facts  # noqa: E402
import permissions as perm  # noqa: E402
import pii_masker as pii  # noqa: E402
from audit_chain import canonical  # noqa: E402

EDITABLE = {"draft", "returned", "blocked", "pending_approval", "approved"}
UNDO_WINDOW = timedelta(seconds=60)
RETRO_WINDOW = timedelta(hours=48)
OUTCOME_STATE = {"READY": "pending_approval", "NEEDS_INFO": "returned",
                 "NEEDS_REVISION": "returned", "BLOCKED": "blocked"}

TEXT_FIELDS = {"title": 200, "description": 4000, "reason": 2000, "impact": 2000,
               "implementation_plan": 4000, "rollback_plan": 2000}
BOOL_DEFAULTS = {"emergency": False, "reversible": True, "production_impact": True,
                 "affects_availability": False, "weakens_security": False,
                 "removes_auth_or_backup": False}
CHANNELS = ("form", "chat", "email", "ticket", "voice")
ASSET_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
PII_TYPES = {"NIK", "PHONE", "EMAIL", "EMP-ID"}  # IP tetap: data infrastruktur


class CabError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class Clock:
    """Jam sistem. `fixed` membekukan waktu (tes, demo 'maju ke rapat CAB')."""

    def __init__(self, fixed=None):
        self.fixed = fixed

    def now(self):
        return self.fixed or datetime.now(timezone.utc)

    def set(self, dt):
        self.fixed = dt


def snapshot(fields):
    return hashlib.sha256(canonical(fields).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# validasi field
# --------------------------------------------------------------------------
def _bad(field, message):
    raise CabError(400, "invalid_field", "%s: %s" % (field, message))


def _text(value, field, limit):
    if value is None:
        return ""
    if not isinstance(value, str):
        _bad(field, "harus teks")
    if len(value) > limit:
        _bad(field, "maksimal %d karakter" % limit)
    return value.strip()


def normalize(data):
    """Field masukan -> (field bersih, ringkasan PII). Field tak dikenal ditolak;
    PII (NIK, telepon, email, EMP-ID) di teks bebas disamarkan sebelum disimpan."""
    if not isinstance(data, dict):
        raise CabError(400, "invalid_fields", "fields harus objek JSON.")
    allowed = set(TEXT_FIELDS) | set(BOOL_DEFAULTS) | {
        "type", "assets", "change_kind", "exposure", "ports", "window", "access", "channel"}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise CabError(400, "unknown_field", "Field tidak dikenal: %s" % ", ".join(unknown))

    out, mask_log = {}, []
    out["type"] = data.get("type") or "change"
    if out["type"] not in ("change", "access"):
        _bad("type", "change atau access")
    for key, limit in TEXT_FIELDS.items():
        masked, log = pii.mask_pii(_text(data.get(key), key, limit), types=PII_TYPES)
        out[key] = masked
        mask_log += log

    assets = data.get("assets") or []
    if not isinstance(assets, list) or len(assets) > 20:
        _bad("assets", "daftar maksimal 20 asset_id")
    out["assets"] = []
    for a in assets:
        a = str(a).strip().lower()
        if not ASSET_RE.match(a):
            _bad("assets", "asset_id tidak valid")
        if a not in out["assets"]:
            out["assets"].append(a)

    out["change_kind"] = data.get("change_kind") or "other"
    if out["change_kind"] not in cab_rules.CHANGE_KINDS:
        _bad("change_kind", "salah satu dari %s" % ", ".join(cab_rules.CHANGE_KINDS))
    out["exposure"] = data.get("exposure") or "none"
    if out["exposure"] not in cab_rules.EXPOSURES:
        _bad("exposure", "none, internal, atau internet")

    ports = data.get("ports") or []
    if (not isinstance(ports, list) or len(ports) > 20
            or any(isinstance(p, bool) or not isinstance(p, int) or not 0 < p < 65536 for p in ports)):
        _bad("ports", "daftar nomor port 1-65535, maksimal 20")
    out["ports"] = sorted(set(ports))

    window = data.get("window")
    if window is not None:
        if not isinstance(window, dict) or set(window) - {"start", "end"}:
            _bad("window", "objek {start, end}")
        window = {k: _text(window.get(k), "window.%s" % k, 40) for k in ("start", "end")}
    out["window"] = window

    access = data.get("access")
    if access is not None:
        if not isinstance(access, dict) or set(access) - {"grantee", "authorizing_role", "expires_at"}:
            _bad("access", "objek {grantee, authorizing_role, expires_at}")
        access = {k: _text(access.get(k), "access.%s" % k, 120)
                  for k in ("grantee", "authorizing_role", "expires_at")}
    out["access"] = access

    for key, default in BOOL_DEFAULTS.items():
        value = data.get(key, default)
        if not isinstance(value, bool):
            _bad(key, "harus true/false")
        out[key] = value
    out["channel"] = data.get("channel") or "form"
    if out["channel"] not in CHANNELS:
        _bad("channel", "salah satu dari %s" % ", ".join(CHANNELS))
    return out, pii.summarize(mask_log)


# --------------------------------------------------------------------------
# store
# --------------------------------------------------------------------------
class CabStore:
    def __init__(self, chain, clock=None, root=None):
        self.chain = chain
        self.clock = clock or Clock()
        self.root = root
        self.lock = threading.RLock()
        self.requests, self.intakes = {}, {}
        for rec in chain.records():
            if str(rec.get("stage", "")).startswith("cab."):
                self._apply(rec)

    # ---- identitas & visibilitas -------------------------------------------
    def actor(self, user):
        """Persona demo dari permissions.csv (nama persis). API tanpa login
        mempercayai nama ini; lihat docs/decisions/0001."""
        name = " ".join(str(user or "").split()).lower()
        row = next((r for r in perm.load_permissions_rows() if r.get("user", "").lower() == name), None)
        if not name or row is None:
            raise CabError(403, "unknown_actor", "Persona tidak dikenal.")
        return {"user": row["user"], "role": row["role"]}

    def _assignees(self, req):
        return {s["assignee"] for s in (req["precheck"] or {}).get("approvals", [])}

    def can_view(self, actor, req):
        return (actor["user"] == req["requester"]["user"] or actor["role"] == "IT Admin"
                or actor["user"] in self._assignees(req))

    def _get(self, cr_id, actor):
        req = self.requests.get(cr_id)
        # tidak ada dan tidak boleh dilihat dijawab sama persis
        if req is None or not self.can_view(actor, req):
            raise CabError(404, "not_found", "Permintaan tidak ditemukan.")
        return req

    # ---- event ---------------------------------------------------------------
    def _emit(self, event, cr_id, actor, state_to, data=None, snap=None):
        req = self.requests.get(cr_id)
        rec = self.chain.append({
            "ts": self.clock.now().isoformat(timespec="seconds"),
            "stage": "cab." + event,
            "actor": actor["user"] if actor else "system",
            "actor_role": actor["role"] if actor else None,
            "cr_id": cr_id,
            "state_from": req["state"] if req else None,
            "state_to": state_to,
            "snapshot_sha256": snap,
            "data": data or {},
        })
        self._apply(rec)
        return rec

    def _deny(self, req, actor, action, status, code, message):
        self._emit("denied", req["id"], actor, req["state"],
                   {"action": action, "code": code, "reason": message})
        raise CabError(status, code, message)

    def _apply(self, rec):
        event, cid, data = rec["stage"][4:], rec.get("cr_id"), rec.get("data") or {}
        if event == "intake":
            self.intakes[data.get("intake_id")] = {"actor": rec.get("actor"), "seq": rec.get("seq")}
            return
        if event == "created":
            self.requests[cid] = {
                "id": cid, "state": "draft", "fields": data["fields"],
                "requester": data["requester"], "created_at": rec["ts"],
                "intake_id": data.get("intake_id"), "pii_masked": data.get("pii_masked", ""),
                "precheck": None, "snapshot": None, "approvals": {}, "rejection": None,
                "dispatch": None, "undo": None, "review": None, "history": [],
            }
        req = self.requests.get(cid)
        if req is None:
            return
        req["history"].append({"seq": rec.get("seq"), "ts": rec["ts"], "event": event,
                               "actor": rec.get("actor"), "state": rec.get("state_to"),
                               "detail": data.get("reason") or data.get("slot") or None,
                               "hash": rec.get("hash")})
        if event == "updated":
            req.update(fields=data["fields"], pii_masked=data.get("pii_masked", ""),
                       precheck=None, snapshot=None, approvals={})
        elif event == "submitted":
            req.update(precheck=data["precheck"], snapshot=rec.get("snapshot_sha256"), approvals={})
        elif event == "approved":
            req["approvals"][data["slot"]] = {"by": rec.get("actor"), "at": rec["ts"],
                                              "mode": data.get("mode"), "meeting": data.get("meeting"),
                                              "note": data.get("note"), "snapshot": rec.get("snapshot_sha256")}
        elif event == "rejected":
            req["rejection"] = {"by": rec.get("actor"), "at": rec["ts"], "reason": data.get("reason")}
        elif event == "dispatched":
            req["dispatch"] = dict(data, at=rec["ts"], by=rec.get("actor"))
        elif event == "undone":
            req["undo"] = {"by": rec.get("actor"), "at": rec["ts"]}
        elif event == "reviewed":
            req["review"] = {"by": rec.get("actor"), "at": rec["ts"], "note": data.get("note")}
        req["state"] = rec.get("state_to") or req["state"]

    # ---- aksi ----------------------------------------------------------------
    def record_intake(self, actor, result):
        """Catat bahwa teks bebas pernah ditafsirkan (oleh LLM atau fallback)."""
        intake_id = "IN-" + uuid.uuid4().hex[:10]
        with self.lock:
            self._emit("intake", None, actor, None, {
                "intake_id": intake_id, "channel": result.get("channel"),
                "input_sha256": result.get("input_sha256"), "llm": result.get("llm"),
                "proposed": result.get("fields"), "dropped": result.get("dropped"),
                "questions": result.get("questions"), "warnings": result.get("warnings")})
        return intake_id

    def create(self, actor, fields, intake_id=None):
        clean, pii_summary = normalize(fields)
        with self.lock:
            if intake_id is not None:
                intake = self.intakes.get(intake_id)
                if intake is None or intake["actor"] != actor["user"]:
                    raise CabError(400, "invalid_intake", "intake_id tidak dikenal.")
            cid = "CR-" + uuid.uuid4().hex[:10]
            self._emit("created", cid, actor, "draft",
                       {"fields": clean, "requester": actor, "intake_id": intake_id,
                        "pii_masked": pii_summary})
            return self.requests[cid]

    def update(self, actor, cr_id, fields):
        clean, pii_summary = normalize(fields)
        with self.lock:
            req = self._get(cr_id, actor)
            if actor["user"] != req["requester"]["user"]:
                self._deny(req, actor, "update", 403, "not_requester", "Hanya pemohon yang bisa mengubah.")
            if req["state"] not in EDITABLE:
                self._deny(req, actor, "update", 409, "not_editable",
                           "Permintaan berstatus %s tidak bisa diubah." % req["state"])
            self._emit("updated", cr_id, actor, "draft",
                       {"fields": clean, "pii_masked": pii_summary,
                        "invalidated_approvals": sorted(req["approvals"])})
            return req

    def submit(self, actor, cr_id):
        with self.lock:
            req = self._get(cr_id, actor)
            if actor["user"] != req["requester"]["user"]:
                self._deny(req, actor, "submit", 403, "not_requester", "Hanya pemohon yang bisa mengajukan.")
            if req["state"] != "draft":
                self._deny(req, actor, "submit", 409, "not_draft",
                           "Hanya draft yang bisa diajukan; ubah dulu permintaan ini.")
            cr = dict(req["fields"], requester=req["requester"])
            result = cab_rules.precheck(cr, self.clock.now(), root=self.root)
            self._emit("submitted", cr_id, actor, OUTCOME_STATE[result["outcome"]],
                       {"precheck": result}, snap=snapshot(req["fields"]))
            return req

    def approve(self, actor, cr_id, slot, meeting=None, note=None):
        with self.lock:
            req = self._get(cr_id, actor)
            if req["state"] != "pending_approval":
                self._deny(req, actor, "approve", 409, "not_pending",
                           "Permintaan tidak sedang menunggu persetujuan.")
            slots = {s["slot"]: s for s in req["precheck"]["approvals"]}
            target = slots.get(slot)
            if target is None:
                self._deny(req, actor, "approve", 400, "unknown_slot", "Slot persetujuan tidak dikenal.")
            if slot in req["approvals"]:
                self._deny(req, actor, "approve", 409, "already_approved", "Slot ini sudah disetujui.")
            if actor["user"] == req["requester"]["user"]:
                self._deny(req, actor, "approve", 403, "self_approval",
                           "Pemohon tidak boleh menyetujui permintaannya sendiri.")
            if actor["user"] != target["assignee"]:
                self._deny(req, actor, "approve", 403, "not_assignee",
                           "Slot %s hanya bisa disetujui %s." % (target["label"], target["assignee"]))
            if snapshot(req["fields"]) != req["snapshot"]:
                self._deny(req, actor, "approve", 409, "stale", "Isi permintaan berubah sejak diajukan.")
            meeting_at = None
            if target["kind"] == "cab_meeting":
                meeting_at = self._valid_meeting(req, actor, meeting)
            data = {"slot": slot, "label": target["label"], "mode": target["mode"],
                    "meeting": meeting_at, "note": _text(note, "note", 1000) or None}
            done = set(req["approvals"]) | {slot}
            state = "approved" if done >= set(slots) else "pending_approval"
            self._emit("approved", cr_id, actor, state, data, snap=req["snapshot"])
            return req

    def _valid_meeting(self, req, actor, meeting):
        planned = cab_rules.parse_time(req["precheck"]["cab_meeting"]["at"])
        when = cab_rules.parse_time(meeting) if meeting else planned
        wib = kb_facts.tz("WIB")
        local = when.astimezone(wib) if when else None
        if (local is None or local.weekday() != cab_rules.CAB_WEEKDAY
                or local.time() != cab_rules.CAB_TIME or when < planned):
            self._deny(req, actor, "approve", 400, "invalid_meeting",
                       "Keputusan CAB harus merujuk rapat Rabu 14:00 WIB mulai %s."
                       % cab_rules.fmt(planned, "WIB"))
        if self.clock.now() < when:
            self._deny(req, actor, "approve", 409, "meeting_not_held",
                       "Keputusan CAB baru bisa dicatat setelah rapat %s." % cab_rules.fmt(when, "WIB"))
        return when.isoformat()

    def reject(self, actor, cr_id, reason):
        with self.lock:
            req = self._get(cr_id, actor)
            open_slots = [s for s in (req["precheck"] or {}).get("approvals", [])
                          if s["slot"] not in req["approvals"] and s["assignee"] == actor["user"]]
            if req["state"] != "pending_approval":
                self._deny(req, actor, "reject", 409, "not_pending",
                           "Permintaan tidak sedang menunggu persetujuan.")
            if not open_slots:
                self._deny(req, actor, "reject", 403, "not_assignee",
                           "Hanya approver yang belum memberi keputusan yang bisa menolak.")
            reason = _text(reason, "reason", 1000)
            if not reason:
                raise CabError(400, "reason_required", "Alasan penolakan wajib diisi.")
            self._emit("rejected", cr_id, actor, "rejected",
                       {"slot": open_slots[0]["slot"], "reason": reason}, snap=req["snapshot"])
            return req

    def _may_operate(self, actor, req):
        return actor["user"] == req["requester"]["user"] or actor["role"] == "IT Admin"

    def dispatch(self, actor, cr_id):
        """Teruskan rencana yang SUDAH disetujui ke mock tool."""
        with self.lock:
            req = self._get(cr_id, actor)
            if not self._may_operate(actor, req):
                self._deny(req, actor, "dispatch", 403, "not_allowed",
                           "Hanya pemohon atau IT Admin yang bisa menjalankan.")
            if req["state"] != "approved":
                self._deny(req, actor, "dispatch", 409, "not_approved",
                           "Belum disetujui semua approver; tidak ada tool yang dijalankan.")
            now = self.clock.now()
            emergency = req["fields"].get("emergency")
            data = {"actions": mock_dispatch(req, self.root),
                    "undo_until": (now + UNDO_WINDOW).isoformat(timespec="seconds"),
                    "retro_due": (now + RETRO_WINDOW).isoformat(timespec="seconds") if emergency else None}
            self._emit("dispatched", cr_id, actor, "retro_review" if emergency else "dispatched",
                       data, snap=req["snapshot"])
            return req

    def undo(self, actor, cr_id):
        with self.lock:
            req = self._get(cr_id, actor)
            if not self._may_operate(actor, req):
                self._deny(req, actor, "undo", 403, "not_allowed",
                           "Hanya pemohon atau IT Admin yang bisa membatalkan.")
            if req["state"] not in ("dispatched", "retro_review") or not req["dispatch"]:
                self._deny(req, actor, "undo", 409, "not_dispatched", "Belum ada yang dijalankan.")
            if self.clock.now() > cab_rules.parse_time(req["dispatch"]["undo_until"]):
                self._deny(req, actor, "undo", 409, "undo_expired", "Batas undo 60 detik sudah lewat.")
            self._emit("undone", cr_id, actor, "undone",
                       {"recalled": [a["id"] for a in req["dispatch"]["actions"]]}, snap=req["snapshot"])
            return req

    def review(self, actor, cr_id, note):
        with self.lock:
            req = self._get(cr_id, actor)
            if req["state"] != "retro_review":
                self._deny(req, actor, "review", 409, "not_in_review", "Tidak sedang menunggu review CAB.")
            if actor["role"] != "HR Manager":
                self._deny(req, actor, "review", 403, "not_cab_chair",
                           "Review retroaktif dicatat oleh acting CAB chair.")
            self._emit("reviewed", cr_id, actor, "closed", {"note": _text(note, "note", 1000) or None},
                       snap=req["snapshot"])
            return req

    def cancel(self, actor, cr_id, reason=None):
        with self.lock:
            req = self._get(cr_id, actor)
            if actor["user"] != req["requester"]["user"]:
                self._deny(req, actor, "cancel", 403, "not_requester", "Hanya pemohon yang bisa membatalkan.")
            if req["state"] not in EDITABLE:
                self._deny(req, actor, "cancel", 409, "not_cancellable",
                           "Permintaan berstatus %s tidak bisa dibatalkan." % req["state"])
            self._emit("cancelled", cr_id, actor, "cancelled", {"reason": _text(reason, "reason", 1000) or None})
            return req

    # ---- baca -----------------------------------------------------------------
    def list_for(self, actor):
        rows = [r for r in self.requests.values() if self.can_view(actor, r)]
        return sorted(rows, key=lambda r: r["created_at"], reverse=True)

    def records_for(self, actor, cr_id):
        """Baris audit mentah (lengkap dengan hash) untuk satu permintaan."""
        self._get(cr_id, actor)
        return [r for r in self.chain.records() if r.get("cr_id") == cr_id]

    def allowed_actions(self, actor, req):
        acts, state, user = [], req["state"], actor["user"]
        mine = user == req["requester"]["user"]
        if mine and state in EDITABLE:
            acts += ["update", "cancel"]
        if mine and state == "draft":
            acts.append("submit")
        if state == "pending_approval" and not mine:
            pending = [s for s in req["precheck"]["approvals"]
                       if s["slot"] not in req["approvals"] and s["assignee"] == user]
            meeting = (req["precheck"].get("cab_meeting") or {}).get("at")
            held = meeting is None or self.clock.now() >= cab_rules.parse_time(meeting)
            acts += ["approve:%s" % s["slot"] for s in pending if s["kind"] != "cab_meeting" or held]
            if pending:
                acts.append("reject")
        if state == "approved" and self._may_operate(actor, req):
            acts.append("dispatch")
        if (state in ("dispatched", "retro_review") and req["dispatch"] and self._may_operate(actor, req)
                and self.clock.now() <= cab_rules.parse_time(req["dispatch"]["undo_until"])):
            acts.append("undo")
        if state == "retro_review" and actor["role"] == "HR Manager":
            acts.append("review")
        return acts


def mock_dispatch(req, root=None):
    """Aksi yang AKAN dikirim ke tool sungguhan. Tidak ada yang benar-benar terkirim."""
    f, pre = req["fields"], req["precheck"]
    people = [req["requester"]["user"]] + [a["by"] for a in req["approvals"].values()]
    attendees = list(dict.fromkeys(people))
    window = f.get("window") or {}
    actions = [
        {"id": "A1", "tool": "calendar.create_event", "status": "would_have_sent",
         "title": "[%s] %s" % (req["id"], f.get("title") or f.get("description", "")[:60]),
         "start": window.get("start"), "end": window.get("end"), "attendees": attendees},
        {"id": "A2", "tool": "ticket.create", "status": "would_have_sent",
         "system": "IT change register", "ref": req["id"], "risk": pre["risk"]["level"],
         "approvals": sorted(req["approvals"])},
    ]
    cmdb = kb_facts.load_cmdb(root)
    if any(cmdb.get(a, {}).get("type") == "Firewall" and cmdb[a].get("site") == "Makassar"
           for a in f.get("assets", [])):
        directory = {p["name"]: p for p in kb_facts.load_directory(root)}
        hendra = directory.get("Hendra Wijaya", {})
        action = {"id": "A3", "tool": "task.create", "status": "would_have_sent",
                  "assignee": req["requester"]["user"],
                  "title": "Telepon branch coordinator sebelum maintenance dimulai",
                  "contact": "Hendra Wijaya", "citations": [cab_rules.Context(root).c("sop7.notify")]}
        if hendra and hendra.get("office") != "Makassar":
            action["warning"] = ("Sumber bertentangan: SOP-7 menyebut Hendra Wijaya untuk Makassar, "
                                 "direktori mencatat %s, kantor %s." % (hendra.get("role"), hendra.get("office")))
        actions.append(action)
    return actions
