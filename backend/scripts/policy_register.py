#!/usr/bin/env python3
"""Policy register Pra-CAB: aturan perusahaan sebagai data, bukan kode.

Satu aturan:
    {id, title, topic, check_id, tier, subject, action, condition, effect,
     approver?, message, pass_message?, basis?, sources[], owner,
     effective_date, supersedes?}

    tier       perusahaan | standar   (perusahaan menutup standar, per topik & aset)
    subject    {asset | zone | site | asset_type}: "*" = semua
    action     "*" | access | change
    condition  semua harus benar (AND); kosong = selalu benar. Daftar nilai
               (departemen penerima, exposure, port, jenis perubahan), atau
               schedule_overlaps {weekdays: [0=Senin..6=Minggu], from: "HH:MM",
               to: "HH:MM", tz?: WIB|WITA|WIT} = jadwal CR beririsan dengan
               jendela harian itu; jam dibaca di `tz`, default waktu lokal site
               aset. schedule_not_within (bentuk sama) = jadwal CR TIDAK
               seluruhnya di dalam satu kejadian jendela itu. CR tanpa jadwal
               valid: aturan jadwal tidak dinilai
    effect     BLOCK | FAIL | WARN | REQUIRE_APPROVER. emergency_effect /
               emergency_message (opsional) dipakai bila CR emergency
    approver   (REQUIRE_APPROVER) "asset_owner" | "cab_meeting" | {role}.
               "cab_meeting" = wajib keputusan rapat CAB; precheck menggabungkannya
               ke satu slot CAB. approver_sources = indeks `sources` yang menjadi
               kutipan slot itu (default: semua)
    sources    kutipan yang diverifikasi ulang setiap kali aturan dipakai:
               {type: doc, doc_id, quote} | {type: cmdb, asset, field, quote?}
               | {type: chat, ts, quote} | {type: submitted, doc_id, quote}

Siklus hidup: draft -> active -> superseded | retired, atau draft -> rejected.
Register efektif = seed (kb/_policies.json: aturan yang dimigrasi dari kode)
+ event `policy.*` di audit chain. Engine hanya memakai aturan `active` yang
effective_date-nya sudah tiba. Aturan yang sumbernya tidak bisa diverifikasi
lagi tidak dipakai dan dilaporkan sebagai WARN, tidak diam-diam diabaikan.
"""

import hashlib
import json
import re
import sys
import threading
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import injection_guard as guard  # noqa: E402
import kb_facts  # noqa: E402
import permissions as perm  # noqa: E402
import pii_masker as pii  # noqa: E402

TIERS = ("perusahaan", "standar")
ACTIONS = ("*", "access", "change")
EFFECTS = ("BLOCK", "FAIL", "WARN", "REQUIRE_APPROVER")
EMERGENCY_EFFECTS = ("BLOCK", "FAIL", "WARN")
APPROVER_KINDS = ("asset_owner", "cab_meeting")
BASES = ("sop", "standar", "interpretasi", "sistem")
SUBJECT_FIELDS = {"asset": "asset_id", "zone": "zone", "site": "site", "asset_type": "type"}
LIST_CONDITIONS = ("grantee_department_in", "grantee_department_not_in", "exposure_in",
                   "ports_any", "change_kind_in")
GRANTEE_CONDITIONS = ("grantee_department_in", "grantee_department_not_in")
SCHEDULE_CONDITION = "schedule_overlaps"
SCHEDULE_CONDITIONS = (SCHEDULE_CONDITION, "schedule_not_within")
CONDITIONS = LIST_CONDITIONS + SCHEDULE_CONDITIONS
HM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
SOURCE_TYPES = ("doc", "cmdb", "chat", "submitted")
STATUS_EFFECT = {"BLOCK": "BLOCK", "FAIL": "FAIL", "WARN": "WARN", "REQUIRE_APPROVER": "WARN"}
ID_RE = re.compile(r"^POL-[0-9a-z]{4,12}$")
CHECK_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]{1,30}$")
TOPIC_RE = re.compile(r"^[a-z][a-z0-9_]{1,40}$")
MAX_SOURCE_TEXT = 20000
PII_TYPES = {"NIK", "PHONE", "EMAIL", "EMP-ID"}


class PolicyError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def rule_hash(rule):
    body = {k: v for k, v in rule.items() if k in RULE_KEYS}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


RULE_KEYS = ("id", "title", "topic", "check_id", "tier", "subject", "action", "condition", "effect",
             "approver", "approver_label", "approver_sources", "message", "pass_title", "pass_message",
             "emergency_effect", "emergency_message", "basis", "sources", "owner", "effective_date", "supersedes")


def seed_path(root=None):
    return kb_facts.kb_root(root) / "_policies.json"  # awalan _ = tidak diindeks search_kb


def load_seed(root=None):
    path = seed_path(root)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("rules", [])


# --------------------------------------------------------------------------
# validasi
# --------------------------------------------------------------------------
def _bad(code, message):
    raise PolicyError(400, code, message)


def _text(rule, key, limit, required=True):
    value = rule.get(key)
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > limit:
        _bad("invalid_rule", "%s wajib teks maksimal %d karakter." % (key, limit))
    return value.strip()


def validate_rule(rule, refs):
    """Aturan masukan -> aturan bersih. `refs` = {assets, zones, sites, types,
    departments, people} untuk menolak nilai yang tidak ada (salah ketik atau
    halusinasi LLM). Tidak memeriksa kutipan; itu tugas verify_sources()."""
    if not isinstance(rule, dict):
        _bad("invalid_rule", "rule harus objek JSON.")
    unknown = sorted(set(rule) - set(RULE_KEYS))
    if unknown:
        _bad("unknown_field", "Field aturan tidak dikenal: %s" % ", ".join(unknown))
    out = {"title": _text(rule, "title", 200), "message": _text(rule, "message", 400)}
    for key, pattern in (("topic", TOPIC_RE), ("check_id", CHECK_ID_RE)):
        value = rule.get(key)
        if not isinstance(value, str) or not pattern.match(value):
            _bad("invalid_rule", "%s tidak valid." % key)
        out[key] = value
    for key, allowed in (("tier", TIERS), ("action", ACTIONS), ("effect", EFFECTS)):
        if rule.get(key) not in allowed:
            _bad("invalid_rule", "%s harus salah satu dari %s." % (key, ", ".join(allowed)))
        out[key] = rule[key]
    if rule.get("basis") is not None and rule["basis"] not in BASES:
        _bad("invalid_rule", "basis harus salah satu dari %s." % ", ".join(BASES))
    out["basis"] = rule.get("basis")

    subject = rule.get("subject")
    if not isinstance(subject, dict) or not subject or set(subject) - set(SUBJECT_FIELDS):
        _bad("invalid_rule", "subject wajib objek dengan kunci asset/zone/site/asset_type.")
    known = {"asset": refs["assets"], "zone": refs["zones"], "site": refs["sites"], "asset_type": refs["types"]}
    for key, value in subject.items():
        if value != "*" and value not in known[key]:
            _bad("unknown_reference", "subject.%s '%s' tidak ada di CMDB." % (key, value))
    out["subject"] = dict(subject)

    condition = rule.get("condition") or {}
    if not isinstance(condition, dict) or set(condition) - set(CONDITIONS):
        _bad("invalid_rule", "condition hanya boleh berisi %s." % ", ".join(CONDITIONS))
    for key, value in condition.items():
        if key in SCHEDULE_CONDITIONS:
            _validate_schedule(value)
            continue
        if not isinstance(value, list) or not value or len(value) > 20:
            _bad("invalid_rule", "condition.%s harus daftar 1-20 nilai." % key)
        if key in GRANTEE_CONDITIONS:
            lower = {d.lower() for d in refs["departments"]}
            missing = [d for d in value if str(d).lower() not in lower]
            if missing:
                _bad("unknown_reference", "Departemen tidak ada di direktori: %s" % ", ".join(map(str, missing)))
        if key == "ports_any" and any(isinstance(p, bool) or not isinstance(p, int) for p in value):
            _bad("invalid_rule", "condition.ports_any harus angka port.")
    if condition and any(k in GRANTEE_CONDITIONS for k in condition) and out["action"] != "access":
        _bad("invalid_rule", "Kondisi departemen penerima hanya untuk action access.")
    out["condition"] = {k: dict(v) if k in SCHEDULE_CONDITIONS else list(v) for k, v in condition.items()}

    if out["effect"] == "REQUIRE_APPROVER":
        approver = rule.get("approver")
        if approver not in APPROVER_KINDS and not (isinstance(approver, dict) and set(approver) == {"role"}):
            _bad("invalid_rule", "approver harus \"asset_owner\", \"cab_meeting\", atau {\"role\": ...}.")
        out["approver"] = approver
        out["approver_label"] = _text(rule, "approver_label", 80, required=False)
    elif rule.get("approver_sources") is not None:
        _bad("invalid_rule", "approver_sources hanya untuk effect REQUIRE_APPROVER.")
    for key, limit in (("pass_title", 200), ("pass_message", 400), ("emergency_message", 400)):
        value = _text(rule, key, limit, required=False)
        if value:
            out[key] = value
    if rule.get("emergency_effect") is not None:
        if rule["emergency_effect"] not in EMERGENCY_EFFECTS:
            _bad("invalid_rule", "emergency_effect harus salah satu dari %s." % ", ".join(EMERGENCY_EFFECTS))
        if out["effect"] == "REQUIRE_APPROVER":
            _bad("invalid_rule", "emergency_effect tidak berlaku untuk REQUIRE_APPROVER.")
        out["emergency_effect"] = rule["emergency_effect"]

    sources = rule.get("sources")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 6:
        _bad("invalid_rule", "sources wajib 1-6 kutipan.")
    out["sources"] = []
    for src in sources:
        if not isinstance(src, dict) or src.get("type") not in SOURCE_TYPES:
            _bad("invalid_rule", "Setiap source butuh type: %s." % ", ".join(SOURCE_TYPES))
        out["sources"].append({k: v for k, v in src.items() if k in ("type", "doc_id", "asset", "field", "ts", "quote")})
    picks = rule.get("approver_sources")
    if picks is not None:
        if (not isinstance(picks, list) or not picks or len(set(picks)) != len(picks)
                or any(isinstance(i, bool) or not isinstance(i, int) or not 0 <= i < len(sources) for i in picks)):
            _bad("invalid_rule", "approver_sources harus indeks unik ke sources (0-%d)." % (len(sources) - 1))
        out["approver_sources"] = list(picks)

    owner = rule.get("owner")
    if owner not in refs["people"]:
        _bad("unknown_reference", "owner harus persona yang terdaftar (pemilik dokumen sumber).")
    out["owner"] = owner
    eff = rule.get("effective_date")
    if eff is not None and not (isinstance(eff, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", eff)):
        _bad("invalid_rule", "effective_date harus YYYY-MM-DD.")
    out["effective_date"] = eff
    sup = rule.get("supersedes")
    if sup is not None and not (isinstance(sup, str) and ID_RE.match(sup)):
        _bad("invalid_rule", "supersedes harus id aturan.")
    out["supersedes"] = sup
    return out


def _validate_schedule(value):
    if not isinstance(value, dict) or not {"weekdays", "from", "to"} <= set(value) <= {"weekdays", "from", "to", "tz"}:
        _bad("invalid_rule", "condition.schedule_overlaps butuh weekdays, from, to (tz opsional).")
    if "tz" in value and value["tz"] not in kb_facts.TZ_OFFSET:
        _bad("invalid_rule", "schedule_overlaps.tz harus salah satu dari %s." % ", ".join(kb_facts.TZ_OFFSET))
    days = value["weekdays"]
    if (not isinstance(days, list) or not 1 <= len(days) <= 7 or len(set(days)) != len(days)
            or any(isinstance(d, bool) or not isinstance(d, int) or not 0 <= d <= 6 for d in days)):
        _bad("invalid_rule", "schedule_overlaps.weekdays harus 1-7 angka unik 0 (Senin) - 6 (Minggu).")
    for key in ("from", "to"):
        if not isinstance(value[key], str) or not HM_RE.match(value[key]):
            _bad("invalid_rule", "schedule_overlaps.%s harus HH:MM." % key)
    if value["from"] == value["to"]:
        _bad("invalid_rule", "schedule_overlaps.from dan to tidak boleh sama.")


def references(root=None):
    cmdb = kb_facts.load_cmdb(root)
    return {"assets": set(cmdb), "zones": {a["zone"] for a in cmdb.values()},
            "sites": {a["site"] for a in cmdb.values()}, "types": {a["type"] for a in cmdb.values()},
            "departments": {p["department"] for p in kb_facts.load_directory(root)},
            "people": {r["user"] for r in perm.load_permissions_rows()}}


# --------------------------------------------------------------------------
# kutipan
# --------------------------------------------------------------------------
def resolve_source(src, docs, cmdb, root=None, submitted=None):
    """Satu source -> kutipan terverifikasi. Raise kb_facts.CitationError."""
    kind = src.get("type")
    if kind == "doc":
        return kb_facts.cite(src.get("doc_id"), src.get("quote") or "", docs=docs)
    if kind == "cmdb":
        return kb_facts.cite_cmdb(src.get("asset"), src.get("field") or "notes", src.get("quote"), cmdb=cmdb)
    if kind == "chat":
        return kb_facts.cite_chat(src.get("ts") or "", src.get("quote") or "", root=root)
    doc = (submitted or {}).get(src.get("doc_id"))
    if doc is None:
        raise kb_facts.CitationError("dokumen %s tidak ada di register" % src.get("doc_id"))
    want = " ".join(str(src.get("quote") or "").split())
    if not want or want not in " ".join(doc["text"].split()):
        raise kb_facts.CitationError("kutipan tidak ditemukan di %s" % src.get("doc_id"))
    return {"doc_id": src["doc_id"], "title": doc["title"], "section": None, "quote": want,
            "effective_date": doc["at"][:10], "owner": doc["owner"]}


def verify_sources(rule, docs, cmdb, root=None, submitted=None):
    return [resolve_source(s, docs, cmdb, root, submitted) for s in rule["sources"]]


# --------------------------------------------------------------------------
# engine
# --------------------------------------------------------------------------
class _Fields(dict):
    def __missing__(self, key):
        return "{%s}" % key


def in_force(rule, day):
    return rule.get("status", "active") == "active" and (rule.get("effective_date") or "") <= day


def applies(rule, cr, asset):
    action = rule["action"]
    if action != "*" and (action == "access") != (cr.get("type") == "access"):
        return False
    return all(v == "*" or asset.get(SUBJECT_FIELDS[k]) == v for k, v in rule["subject"].items())


def cr_window(cr):
    """(start, end) jadwal CR, atau None bila kosong/tanpa zona/terbalik."""
    w = cr.get("window") or {}
    start, end = kb_facts.parse_time(w.get("start")), kb_facts.parse_time(w.get("end"))
    return (start, end) if start and end and start < end else None


def _schedule_args(cond, cr, asset):
    """(start, end, zona, from, to, weekdays) untuk helper waktu kb_facts, atau
    None bila CR tanpa jadwal valid. Jam jendela dibaca di zona `cond.tz` bila
    ada, selain itu waktu lokal site aset."""
    window = cr_window(cr)
    if not window:
        return None

    def hm(text):
        return tuple(int(x) for x in text.split(":"))

    zone = kb_facts.tz(cond["tz"]) if cond.get("tz") else kb_facts.site_tz(asset.get("site"))
    return window[0], window[1], zone, hm(cond["from"]), hm(cond["to"]), set(cond["weekdays"])


def schedule_hit(cond, cr, asset):
    """Kejadian pertama jendela `cond` yang beririsan dengan jadwal CR."""
    args = _schedule_args(cond, cr, asset)
    return kb_facts.daily_overlap(*args) if args else None


def schedule_within(cond, cr, asset):
    """True bila jadwal CR seluruhnya di dalam satu kejadian jendela `cond`."""
    args = _schedule_args(cond, cr, asset)
    return bool(args) and kb_facts.inside_daily(*args)


def holds(condition, cr, department, asset=None):
    for key, values in condition.items():
        if key == SCHEDULE_CONDITION:
            ok = schedule_hit(values, cr, asset or {}) is not None
        elif key == "schedule_not_within":
            ok = cr_window(cr) is not None and not schedule_within(values, cr, asset or {})
        elif key == "grantee_department_in":
            ok = (department or "").lower() in {str(v).lower() for v in values}
        elif key == "grantee_department_not_in":
            ok = (department or "").lower() not in {str(v).lower() for v in values}
        elif key == "exposure_in":
            ok = cr.get("exposure") in values
        elif key == "ports_any":
            ok = bool(set(cr.get("ports") or []) & set(values))
        else:
            ok = cr.get("change_kind") in values
        if not ok:
            return False
    return True


def evaluate(cr, assets, ctx, day):
    """Cocokkan aturan aktif ke CR. Mengembalikan (cek, slot approver, aturan dipakai).

    `ctx` butuh: rules, docs, cmdb, root, submitted, staff(name), person(role).
    Precedence per (topic, aset): aturan perusahaan yang berlaku menutup standar."""
    rules = [r for r in ctx.rules if in_force(r, day)]
    grantee = str((cr.get("access") or {}).get("grantee") or "").strip()
    person = ctx.staff(grantee) if grantee else None
    department = person.get("department") if person else None
    checks, slots, used = [], [], []
    unknown_reported = False
    # aturan per site/zona dievaluasi per aset, dan beberapa aturan bisa memberi
    # temuan yang sama (mis. jendela WMS untuk tiga aset): yang identik cukup sekali
    shown = set()

    def show(check):
        key = (check["id"], check["status"], check["title"], check["detail"],
               json.dumps(check["citations"], sort_keys=True, ensure_ascii=False))
        if key not in shown:
            shown.add(key)
            checks.append(check)

    for topic in sorted({r["topic"] for r in rules}):
        for asset in assets:
            fits = [r for r in rules if r["topic"] == topic and applies(r, cr, asset)]
            chosen = [r for r in fits if r["tier"] == "perusahaan"] or [r for r in fits if r["tier"] == "standar"]
            for rule in chosen:
                if any(k in SCHEDULE_CONDITIONS for k in rule["condition"]) and not cr_window(cr):
                    continue  # tanpa jadwal valid aturan jadwal tidak bisa dinilai; FIELDS sudah memintanya
                if any(k in GRANTEE_CONDITIONS for k in rule["condition"]):
                    if not grantee:
                        continue  # cek ACCESS sudah meminta penerima
                    if person is None:
                        if not unknown_reported:
                            checks.append(_check(rule["check_id"], "NEEDS_INFO", "Penerima akses tidak dikenal",
                                                 "'%s' tidak ada di direktori staf. Tulis nama lengkap seperti "
                                                 "di direktori." % grantee, "sistem", [], None))
                            unknown_reported = True
                        continue
                try:
                    cites = verify_sources(rule, ctx.docs, ctx.cmdb, ctx.root, ctx.submitted)
                except kb_facts.CitationError as exc:
                    checks.append(_check(rule["check_id"], "WARN", "Aturan %s tidak dipakai" % rule["id"],
                                         "Sumber aturan tidak bisa diverifikasi lagi (%s). Minta owner (%s) "
                                         "meninjau aturan ini." % (exc, rule["owner"]), "sistem", [], rule["id"]))
                    continue
                allowed = rule["condition"].get("grantee_department_not_in") or \
                    rule["condition"].get("grantee_department_in") or []
                schedule = rule["condition"].get(SCHEDULE_CONDITION)
                hit = schedule_hit(schedule, cr, asset) if schedule else None
                fields = _Fields(asset=asset["asset_id"], zone=asset.get("zone"), site=asset.get("site"),
                                 grantee=grantee, department=department or "-", allowed=", ".join(allowed),
                                 owner=kb_facts.owner_name(asset.get("owner")) or "-",
                                 overlap=kb_facts.fmt(hit[0]) if hit else "-")
                basis = rule.get("basis") or ("standar" if rule["tier"] == "standar" else "sop")
                triggered = holds(rule["condition"], cr, department, asset)
                used.append({"id": rule["id"], "topic": topic, "tier": rule["tier"], "asset": asset["asset_id"],
                             "triggered": triggered, "rule_sha256": rule_hash(rule)})
                if triggered:
                    # emergency boleh menurunkan efek (mis. FAIL -> WARN) dan mengganti pesannya
                    urgent = bool(cr.get("emergency"))
                    effect = rule.get("emergency_effect") if urgent and rule.get("emergency_effect") else rule["effect"]
                    message = rule.get("emergency_message") if urgent and rule.get("emergency_message") \
                        else rule["message"]
                    show(_check(rule["check_id"], STATUS_EFFECT[effect], rule["title"].format_map(fields),
                                message.format_map(fields), basis, cites, rule["id"]))
                    if effect == "REQUIRE_APPROVER":
                        picked = [cites[i] for i in rule["approver_sources"]] if rule.get("approver_sources") else cites
                        if rule["approver"] == "cab_meeting":
                            # penanda; precheck menggabungkan semua alasan CAB ke satu slot rapat
                            slots.append({"slot": "cab", "label": rule.get("approver_label") or "Keputusan rapat CAB",
                                          "assignee": None, "kind": "cab_meeting", "mode": "tertulis",
                                          "citations": picked, "rule_id": rule["id"]})
                            continue
                        who = (kb_facts.owner_name(asset.get("owner")) if rule["approver"] == "asset_owner"
                               else ctx.person(rule["approver"]["role"]))
                        if who:
                            slots.append({"slot": "owner:%s" % who if rule["approver"] == "asset_owner"
                                          else "policy:%s" % rule["id"],
                                          "label": rule.get("approver_label") or "Approver aturan %s" % rule["id"],
                                          "assignee": who, "kind": "person", "mode": "tertulis",
                                          "citations": picked, "rule_id": rule["id"]})
                elif rule.get("pass_message"):
                    show(_check(rule["check_id"], "PASS",
                                (rule.get("pass_title") or rule["title"]).format_map(fields),
                                rule["pass_message"].format_map(fields), basis, cites[:1], rule["id"]))
    return checks, slots, used


def _check(cid, status, title, detail, basis, citations, rule_id):
    out = {"id": cid, "status": status, "title": title, "detail": detail, "basis": basis,
           "citations": list(citations)}
    if rule_id:
        out["rule_id"] = rule_id
    return out


# --------------------------------------------------------------------------
# store: seed + event di audit chain
# --------------------------------------------------------------------------
class PolicyStore:
    def __init__(self, chain, clock, root=None):
        self.chain, self.clock, self.root = chain, clock, root
        self.lock = threading.RLock()
        self.rules, self.sources = {}, {}
        for rule in load_seed(root):
            self.rules[rule["id"]] = dict(rule, status="active", origin="seed", history=[])
        for rec in chain.records():
            if str(rec.get("stage", "")).startswith("policy."):
                self._apply(rec)

    # ---- baca ---------------------------------------------------------------
    def active_rules(self):
        return [r for r in self.rules.values() if r["status"] == "active"]

    def get(self, policy_id):
        rule = self.rules.get(policy_id)
        if rule is None:
            raise PolicyError(404, "not_found", "Aturan tidak ditemukan.")
        return rule

    def allowed_actions(self, actor, rule):
        acts = []
        if rule["status"] == "draft" and actor["user"] == rule["owner"] and actor["user"] != rule.get("proposed_by"):
            acts += ["approve", "reject"]
        if rule["status"] == "active" and actor["user"] == rule["owner"]:
            acts.append("retire")
        return acts

    def _verify_ctx(self):
        root = kb_facts.kb_root(self.root)
        return kb_facts._documents(root), kb_facts.load_cmdb(root), root

    # ---- event --------------------------------------------------------------
    def _emit(self, event, policy_id, actor, data):
        rec = self.chain.append({
            "ts": self.clock.now().isoformat(timespec="seconds"), "stage": "policy." + event,
            "actor": actor["user"] if actor else "system", "actor_role": actor["role"] if actor else None,
            "policy_id": policy_id, "data": data})
        self._apply(rec)
        return rec

    def _deny(self, rule, actor, action, status, code, message):
        self._emit("denied", rule["id"], actor, {"action": action, "code": code, "reason": message})
        raise PolicyError(status, code, message)

    def _apply(self, rec):
        event, pid, data = rec["stage"][7:], rec.get("policy_id"), rec.get("data") or {}
        if event == "source":
            self.sources[data["doc_id"]] = {"title": data["title"], "text": data["text"], "owner": data["owner"],
                                            "sha256": data["sha256"], "by": rec.get("actor"), "at": rec["ts"]}
            return
        if event == "proposed":
            self.rules[pid] = dict(data["rule"], id=pid, status="draft", origin=data.get("origin", "manual"),
                                   proposed_by=rec.get("actor"), proposed_at=rec["ts"], history=[],
                                   llm=data.get("llm"))
        rule = self.rules.get(pid)
        if rule is None:
            return
        rule["history"].append({"seq": rec.get("seq"), "ts": rec["ts"], "event": event,
                                "actor": rec.get("actor"), "detail": data.get("reason"), "hash": rec.get("hash")})
        if event == "approved":
            rule.update(status="active", approved_by=rec.get("actor"), approved_at=rec["ts"],
                        effective_date=data.get("effective_date") or rule.get("effective_date"))
            old = self.rules.get(rule.get("supersedes"))
            if old is not None:
                old.update(status="superseded", superseded_by=pid)
        elif event == "rejected":
            rule.update(status="rejected", rejected_by=rec.get("actor"), reason=data.get("reason"))
        elif event == "retired":
            rule.update(status="retired", retired_by=rec.get("actor"), reason=data.get("reason"))

    # ---- aksi ---------------------------------------------------------------
    def add_source(self, actor, title, text, owner):
        """Simpan dokumen sumber (memo, SOP baru) yang belum ada di KB."""
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise PolicyError(400, "invalid_title", "Judul dokumen wajib, maksimal 200 karakter.")
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_SOURCE_TEXT:
            raise PolicyError(400, "invalid_text", "Teks dokumen wajib, maksimal %d karakter." % MAX_SOURCE_TEXT)
        if owner not in references(self.root)["people"]:
            raise PolicyError(400, "unknown_reference", "owner harus persona yang terdaftar.")
        if guard.detect_injection(text, scope="evidence")["action"] == "BLOCK":
            raise PolicyError(400, "source_injection", "Dokumen memuat instruksi yang ditujukan ke AI/sistem; "
                                                       "tidak diterima sebagai sumber aturan.")
        masked, _ = pii.mask_pii(text.strip(), types=PII_TYPES)
        doc_id = "DOC-" + uuid.uuid4().hex[:8]
        with self.lock:
            self._emit("source", None, actor, {"doc_id": doc_id, "title": title.strip(), "text": masked,
                                               "owner": owner,
                                               "sha256": hashlib.sha256(masked.encode("utf-8")).hexdigest()})
        return doc_id

    def propose(self, actor, rule, origin="manual", llm=None):
        clean = validate_rule(rule, references(self.root))
        docs, cmdb, root = self._verify_ctx()
        try:
            verify_sources(clean, docs, cmdb, root, self.sources)
        except kb_facts.CitationError as exc:
            raise PolicyError(400, "unverified_source", "Kutipan aturan tidak ditemukan di sumbernya: %s" % exc)
        with self.lock:
            if clean["supersedes"] and self.rules.get(clean["supersedes"], {}).get("status") != "active":
                raise PolicyError(400, "invalid_supersedes", "supersedes harus aturan yang aktif.")
            pid = "POL-" + uuid.uuid4().hex[:8]
            self._emit("proposed", pid, actor, {"rule": clean, "origin": origin, "llm": llm})
            return self.rules[pid]

    def approve(self, actor, policy_id):
        with self.lock:
            rule = self.get(policy_id)
            if rule["status"] != "draft":
                self._deny(rule, actor, "approve", 409, "not_draft", "Hanya draft yang bisa disahkan.")
            if actor["user"] == rule.get("proposed_by"):
                self._deny(rule, actor, "approve", 403, "self_approval",
                           "Pengusul tidak boleh mengesahkan aturannya sendiri.")
            if actor["user"] != rule["owner"]:
                self._deny(rule, actor, "approve", 403, "not_owner",
                           "Aturan ini hanya bisa disahkan pemilik dokumen sumbernya (%s)." % rule["owner"])
            docs, cmdb, root = self._verify_ctx()
            try:
                verify_sources(rule, docs, cmdb, root, self.sources)
            except kb_facts.CitationError as exc:
                self._deny(rule, actor, "approve", 409, "unverified_source",
                           "Sumber aturan tidak bisa diverifikasi lagi: %s" % exc)
            if rule.get("supersedes") and self.rules.get(rule["supersedes"], {}).get("status") != "active":
                self._deny(rule, actor, "approve", 409, "invalid_supersedes", "Aturan yang digantikan sudah tidak aktif.")
            day = self.clock.now().astimezone(kb_facts.tz("WIB")).date().isoformat()
            self._emit("approved", policy_id, actor, {"effective_date": rule.get("effective_date") or day,
                                                      "rule_sha256": rule_hash(rule)})
            return rule

    def reject(self, actor, policy_id, reason):
        with self.lock:
            rule = self.get(policy_id)
            if rule["status"] != "draft":
                self._deny(rule, actor, "reject", 409, "not_draft", "Hanya draft yang bisa ditolak.")
            if actor["user"] != rule["owner"]:
                self._deny(rule, actor, "reject", 403, "not_owner", "Hanya pemilik dokumen sumber yang bisa menolak.")
            if not isinstance(reason, str) or not reason.strip():
                raise PolicyError(400, "reason_required", "Alasan penolakan wajib diisi.")
            self._emit("rejected", policy_id, actor, {"reason": reason.strip()[:1000]})
            return rule

    def retire(self, actor, policy_id, reason):
        with self.lock:
            rule = self.get(policy_id)
            if rule["status"] != "active":
                self._deny(rule, actor, "retire", 409, "not_active", "Hanya aturan aktif yang bisa dipensiunkan.")
            if actor["user"] != rule["owner"]:
                self._deny(rule, actor, "retire", 403, "not_owner", "Hanya pemilik aturan yang bisa memensiunkan.")
            if not isinstance(reason, str) or not reason.strip():
                raise PolicyError(400, "reason_required", "Alasan wajib diisi.")
            self._emit("retired", policy_id, actor, {"reason": reason.strip()[:1000]})
            return rule
