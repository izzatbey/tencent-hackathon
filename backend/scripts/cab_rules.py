#!/usr/bin/env python3
"""Rule engine Pra-CAB: cek change request terhadap SOP-14 dan dokumen terkait.

precheck(cr, submitted_at) sepenuhnya deterministik, tanpa LLM. Hasilnya
disimpan utuh di audit log saat permintaan diajukan, jadi keputusan bisa
diputar ulang persis seperti saat itu walaupun KB berubah kemudian.

Setiap cek: {id, status, title, detail, basis, citations}
  status  INFO | PASS | WARN | NEEDS_INFO | FAIL | BLOCK
  basis   sop          bunyi dokumen apa adanya
          interpretasi tafsiran tim atas dokumen; perlu disahkan owner dokumen
          sistem       aturan aplikasi yang belum ada di SOP

Outcome (urutan prioritas): BLOCKED > NEEDS_INFO > NEEDS_REVISION > READY
"""

import sys
from datetime import datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import injection_guard as guard  # noqa: E402
import kb_facts  # noqa: E402
import permissions as perm  # noqa: E402

ENGINE = "sop14-v1"
RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
CHANGE_KINDS = ("firewall_rule", "firmware_upgrade", "config_change", "software_install",
                "access_grant", "backup_change", "auth_change", "decommission", "other")
EXPOSURES = ("none", "internal", "internet")

# interpretasi: segmen yang kolom "Internet Access"-nya "No" di TOPO-SEGMENTS
SENSITIVE_ZONES = {"hr-data", "server-farm-jkt", "mgmt"}
# interpretasi: firmware upgrade & dekomisi memutus layanan
AVAILABILITY_KINDS = {"firmware_upgrade", "decommission"}
# TOPO-WMS-WINDOW menyebut fw-edge-mks-01 & vpn-gw-jkt-01; wms-mks-01 ditambahkan (interpretasi)
WMS_ASSETS = {"fw-edge-mks-01", "vpn-gw-jkt-01", "wms-mks-01"}
PRAYER = {"Jakarta": ((11, 30), (13, 0)), "Makassar": ((11, 0), (12, 30))}
OFFICE_HOURS = {"Jakarta": ((8, 0), (17, 0)), "Makassar": ((8, 0), (17, 0)),
                "Jayapura": ((7, 30), (16, 30))}
WEEKDAYS = {0, 1, 2, 3, 4}
CAB_WEEKDAY, CAB_TIME, CAB_LEAD = 2, time(14, 0), timedelta(hours=48)
MEMO_TS = "2026-10-01T09:00:00+07:00"

STATUS_RANK = {"INFO": 0, "PASS": 0, "WARN": 1, "FAIL": 2, "NEEDS_INFO": 3, "BLOCK": 4}

# kunci -> sumber. ("doc", doc_id, teks) | ("cmdb", asset, field, teks) | ("chat", ts, teks)
SOURCES = {
    "sop14.fields": ("doc", "SOP-14", "Submit via the IT change management system with: description, reason, impact assessment, implementation plan, rollback plan, and requested implementation time."),
    "sop14.cab": ("doc", "SOP-14", "The Change Advisory Board (CAB) meets weekly on Wednesdays 14:00 WIB. Requests must be submitted at least 48 hours before the CAB meeting."),
    "sop14.emergency": ("doc", "SOP-14", "Emergency changes: May bypass CAB but must be retroactively reviewed within 48 hours. Requires verbal approval from both the IT Admin and the system owner."),
    "sop14.low": ("doc", "SOP-14", "LOW: No impact on production, reversible, off-hours"),
    "sop14.medium": ("doc", "SOP-14", "MEDIUM: Limited impact, recoverable, requires follow-up verification"),
    "sop14.high": ("doc", "SOP-14", "HIGH: Touches sensitive zone, affects availability, or weakens security controls"),
    "sop14.critical": ("doc", "SOP-14", "CRITICAL: Exposes crown-jewel systems, removes authentication/backup, or is effectively irreversible"),
    "sop14.appr.low": ("doc", "SOP-14", "LOW: IT Admin"),
    "sop14.appr.medium": ("doc", "SOP-14", "MEDIUM: System owner + IT Admin"),
    "sop14.appr.high": ("doc", "SOP-14", "HIGH/CRITICAL: CAB + HR Manager (acting CAB chair)"),
    "ctrl12.fields": ("doc", "CTRL-12", "Change requests must document: what, why, impact assessment, rollback plan, and approver."),
    "ctrl12.emergency": ("doc", "CTRL-12", "Emergency changes may bypass CAB but must be retroactively reviewed within 48 hours."),
    "ctrl01.access": ("doc", "CTRL-01", "any change granting new network or system access must name the requester, the authorizing role, and an expiry date."),
    "ctrl09.exposure": ("doc", "CTRL-09", "direct internet exposure of internal databases or servers is prohibited."),
    "ctrl09.nat": ("doc", "CTRL-09", "Port forwarding or NAT rules exposing internal services to the internet must be classified as HIGH or CRITICAL risk."),
    "ctrl09.ssh": ("doc", "CTRL-09", "SSH (port 22) from the internet to any internal server is classified as CRITICAL risk"),
    "topo.hr-data": ("doc", "TOPO-SEGMENTS", "hr-data | HR Data VLAN | VLAN 99 | HR database only. Segregated. | No. Direct internet exposure PROHIBITED."),
    "topo.server-farm-jkt": ("doc", "TOPO-SEGMENTS", "server-farm-jkt | Server Farm | VLAN 30 | Production servers (ERP, DB, K8s) | No direct exposure. Behind reverse proxy."),
    "topo.mgmt": ("doc", "TOPO-SEGMENTS", "mgmt | Management Network | VLAN 40 | Monitoring, backup, admin access | No. Jump-host access only."),
    "wms.schedule": ("doc", "TOPO-WMS-WINDOW", "Schedule: 23:00 WIB – 02:00 WIB (daily)"),
    "wms.avoid": ("doc", "TOPO-WMS-WINDOW", "Avoid scheduling network changes on fw-edge-mks-01 or vpn-gw-jkt-01 during this window."),
    "sop7.cab": ("doc", "SOP-7", "CAB approval is required for changes that affect the replication window (23:00–02:00 WIB)."),
    "sop7.window": ("doc", "SOP-7", "Remote maintenance of branch firewalls is allowed any weekday (Monday–Friday) between 21:00 and 06:00 local branch time."),
    "sop7.verbal": ("doc", "SOP-7", "Verbal approval from the on-call IT admin or ops manager is sufficient for routine maintenance"),
    "sop7.notify": ("doc", "SOP-7", "Notify the branch coordinator (Hendra Wijaya for Makassar) by phone before commencing maintenance."),
    "memo.cab": ("chat", MEMO_TS, "Approval verbal tidak cukup lagi, wajib CAB written approval."),
    "memo.mfa": ("chat", MEMO_TS, "Wajib via jump-host dengan MFA."),
    "cmdb.fw-mks.mfa": ("cmdb", "fw-edge-mks-01", "notes", "Remote changes require MFA jump-host."),
    "prayer.Jakarta": ("doc", "TOPO-PRAYER-TIMES", "Jakarta (WIB): 11:30 – 13:00 WIB — offices closed, no meetings should be scheduled"),
    "prayer.Makassar": ("doc", "TOPO-PRAYER-TIMES", "Makassar (WITA): 11:00 – 12:30 WITA — offices closed, no meetings should be scheduled"),
    "prayer.flag": ("doc", "TOPO-PRAYER-TIMES", "Any change request or meeting proposed during these windows should be flagged."),
    "office.Jakarta": ("doc", "TOPO-OFFICE-HOURS", "Jakarta HQ: 08:00 – 17:00 WIB"),
    "office.Makassar": ("doc", "TOPO-OFFICE-HOURS", "Makassar Branch: 08:00 – 17:00 WITA"),
    "office.Jayapura": ("doc", "TOPO-OFFICE-HOURS", "Jayapura Branch: 07:30 – 16:30 WIT"),
}


class Context:
    """Data KB yang dibaca sekali per precheck (KB baru langsung terpakai)."""

    def __init__(self, root=None):
        self.root = kb_facts.kb_root(root)
        self.docs = kb_facts._documents(self.root)
        self.cmdb = kb_facts.load_cmdb(self.root)
        self.people = perm.load_permissions_rows()
        self._cache = {}

    def c(self, key):
        if key not in self._cache:
            src = SOURCES[key]
            if src[0] == "doc":
                self._cache[key] = kb_facts.cite(src[1], src[2], docs=self.docs)
            elif src[0] == "cmdb":
                self._cache[key] = kb_facts.cite_cmdb(src[1], src[2], src[3], cmdb=self.cmdb)
            else:
                self._cache[key] = kb_facts.cite_chat(src[1], src[2], root=self.root)
        return self._cache[key]

    def cites(self, *keys):
        return [self.c(k) for k in keys]

    def person(self, role):
        row = next((r for r in self.people if r.get("role") == role), None)
        return row["user"] if row else None


# --------------------------------------------------------------------------
# waktu
# --------------------------------------------------------------------------
def parse_time(value):
    """ISO-8601 berzona -> datetime; None bila kosong/tidak valid/tanpa zona."""
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    return dt if dt.tzinfo else None


def daily_overlap(start, end, tzinfo, from_hm, to_hm, weekdays=None):
    """Kejadian pertama jendela harian [from, to) (waktu lokal `tzinfo`) yang
    beririsan dengan [start, end). `to` < `from` = melewati tengah malam."""
    s, e = start.astimezone(tzinfo), end.astimezone(tzinfo)
    day = s.date() - timedelta(days=1)
    while day <= e.date():
        ws = datetime.combine(day, time(*from_hm), tzinfo)
        we = datetime.combine(day, time(*to_hm), tzinfo)
        if we <= ws:
            we += timedelta(days=1)
        if (weekdays is None or ws.weekday() in weekdays) and ws < e and s < we:
            return ws, we
        day += timedelta(days=1)
    return None


def inside_daily(start, end, tzinfo, from_hm, to_hm, weekdays):
    """True bila [start, end) seluruhnya di dalam satu kejadian jendela harian."""
    s = start.astimezone(tzinfo)
    for day in (s.date() - timedelta(days=1), s.date()):
        ws = datetime.combine(day, time(*from_hm), tzinfo)
        we = datetime.combine(day, time(*to_hm), tzinfo)
        if we <= ws:
            we += timedelta(days=1)
        if ws.weekday() in weekdays and ws <= start and end <= we:
            return True
    return False


def next_cab_meeting(submitted_at):
    """Rapat CAB (Rabu 14:00 WIB) pertama yang >= 48 jam setelah pengajuan."""
    wib = kb_facts.tz("WIB")
    earliest = submitted_at.astimezone(wib) + CAB_LEAD
    day = earliest.date()
    while True:
        meeting = datetime.combine(day, CAB_TIME, wib)
        if day.weekday() == CAB_WEEKDAY and meeting >= earliest:
            return meeting
        day += timedelta(days=1)


HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def fmt(dt, tzname=None):
    """'Rabu 04 Nov 2026 14:00 WIB' (tanpa bergantung locale OS)."""
    if tzname:
        dt = dt.astimezone(kb_facts.tz(tzname))
    return "%s %02d %s %d %s %s" % (HARI[dt.weekday()], dt.day, BULAN[dt.month - 1], dt.year,
                                     dt.strftime("%H:%M"), dt.tzname() or "")


# --------------------------------------------------------------------------
# precheck
# --------------------------------------------------------------------------
REQUIRED_FIELDS = [("description", "deskripsi perubahan"), ("reason", "alasan"),
                   ("impact", "analisis dampak"), ("implementation_plan", "rencana implementasi"),
                   ("rollback_plan", "rencana rollback")]
ACCESS_FIELDS = [("grantee", "penerima akses"), ("authorizing_role", "role pemberi otorisasi"),
                 ("expires_at", "tanggal kedaluwarsa")]
FREE_TEXT = ("title", "description", "reason", "impact", "implementation_plan", "rollback_plan")


def _check(cid, status, title, detail, basis, citations=()):
    return {"id": cid, "status": status, "title": title, "detail": detail,
            "basis": basis, "citations": list(citations)}


def classify_risk(cr, assets, window, ctx):
    """Tingkat risiko SOP-14 §4 + alasan. Level = alasan tertinggi."""
    reasons = []

    def add(level, criterion, keys, basis):
        reasons.append({"level": level, "criterion": criterion, "basis": basis,
                        "citations": ctx.cites(*keys)})

    kind = cr.get("change_kind")
    if cr.get("exposure") == "internet":
        if 22 in (cr.get("ports") or []):
            add("CRITICAL", "SSH (port 22) dibuka dari internet", ["ctrl09.ssh"], "sop")
        critical = [a["asset_id"] for a in assets if a.get("criticality") == "critical"]
        if critical:
            add("CRITICAL", "mengekspos aset ber-criticality critical di CMDB (%s) ke internet"
                % ", ".join(critical), ["sop14.critical"], "interpretasi")
        add("HIGH", "membuka layanan internal ke internet", ["ctrl09.nat"], "sop")
    if cr.get("removes_auth_or_backup"):
        add("CRITICAL", "menghapus autentikasi atau backup", ["sop14.critical"], "sop")
    if cr.get("reversible") is False:
        add("CRITICAL", "pemohon menyatakan perubahan tidak bisa dikembalikan", ["sop14.critical"], "sop")
    sensitive = sorted({a["zone"] for a in assets if a.get("zone") in SENSITIVE_ZONES})
    if sensitive:
        add("HIGH", "menyentuh zona sensitif: %s" % ", ".join(sensitive), ["sop14.high"], "interpretasi")
    if cr.get("affects_availability"):
        add("HIGH", "pemohon menyatakan ketersediaan layanan terdampak", ["sop14.high"], "sop")
    elif kind in AVAILABILITY_KINDS:
        add("HIGH", "jenis perubahan %s memutus layanan selama pengerjaan" % kind,
            ["sop14.high"], "interpretasi")
    if cr.get("weakens_security"):
        add("HIGH", "pemohon menyatakan kontrol keamanan melemah", ["sop14.high"], "sop")

    if not reasons:
        office = office_overlap(assets, window) if window else None
        if cr.get("production_impact") is False and cr.get("reversible", True) and window and not office:
            add("LOW", "tanpa dampak produksi, bisa dikembalikan, di luar jam kerja", ["sop14.low"], "sop")
        else:
            why = "menyentuh aset produksi di CMDB"
            if cr.get("production_impact") is False and office:
                why = "dikerjakan di jam kerja %s" % office
            add("MEDIUM", why, ["sop14.medium"], "interpretasi")

    level = max((r["level"] for r in reasons), key=RISK_LEVELS.index)
    return level, reasons


def office_overlap(assets, window):
    """Nama site pertama yang jam kerjanya (Senin-Jumat) beririsan dengan jendela."""
    start, end = window
    for site in sorted({a.get("site") for a in assets if a.get("site") in OFFICE_HOURS}):
        hours = OFFICE_HOURS[site]
        if daily_overlap(start, end, kb_facts.site_tz(site), hours[0], hours[1], WEEKDAYS):
            return site
    return None


def approval_slots(level, assets, cr, ctx):
    """Slot persetujuan SOP-14 §5 (atau §3 untuk emergency)."""
    it_admin, chair = ctx.person("IT Admin"), ctx.person("HR Manager")
    owners = []
    for a in assets:
        name = kb_facts.owner_name(a.get("owner"))
        if name and name not in owners:
            owners.append(name)

    def person(slot, label, who, keys, mode="tertulis"):
        return {"slot": slot, "label": label, "assignee": who, "kind": "person",
                "mode": mode, "citations": ctx.cites(*keys)}

    if cr.get("emergency"):
        slots = [person("it_admin", "IT Admin", it_admin, ["sop14.emergency"], "lisan")]
        slots += [person("owner:%s" % o, "System owner", o, ["sop14.emergency"], "lisan") for o in owners]
        return slots
    if level == "LOW":
        return [person("it_admin", "IT Admin", it_admin, ["sop14.appr.low"])]
    if level == "MEDIUM":
        slots = [person("owner:%s" % o, "System owner", o, ["sop14.appr.medium"]) for o in owners]
        return slots + [person("it_admin", "IT Admin", it_admin, ["sop14.appr.medium"])]
    return [cab_slot(chair, ["sop14.appr.high"], ctx),
            person("cab_chair", "HR Manager (acting CAB chair)", chair, ["sop14.appr.high"])]


def cab_slot(chair, keys, ctx):
    return {"slot": "cab", "label": "Keputusan rapat CAB (dicatat CAB chair)", "assignee": chair,
            "kind": "cab_meeting", "mode": "tertulis", "citations": ctx.cites(*keys)}


def precheck(cr, submitted_at, root=None, ctx=None):
    ctx = ctx or Context(root)
    checks = []
    extra_cab = []           # alasan tambahan yang mewajibkan keputusan CAB
    emergency = bool(cr.get("emergency"))

    # --- aset -------------------------------------------------------------
    asset_ids = [a for a in (cr.get("assets") or []) if isinstance(a, str)]
    assets = [ctx.cmdb[a] for a in asset_ids if a in ctx.cmdb]
    unknown = [a for a in asset_ids if a not in ctx.cmdb]
    if not asset_ids:
        checks.append(_check("ASSETS", "NEEDS_INFO", "Aset yang diubah",
                             "Sebutkan asset_id CMDB yang terdampak.", "sistem"))
    elif unknown:
        checks.append(_check("ASSETS", "NEEDS_INFO", "Aset yang diubah",
                             "Tidak dikenal di CMDB: %s. Pakai asset_id CMDB." % ", ".join(unknown),
                             "sistem"))
    else:
        checks.append(_check("ASSETS", "PASS", "Aset yang diubah",
                             ", ".join("%s (%s, %s)" % (a["asset_id"], a["zone"], a["criticality"])
                                       for a in assets), "sistem"))

    # --- kelengkapan (SOP-14 §1, CTRL-12) ------------------------------------
    missing = [label for key, label in REQUIRED_FIELDS if not str(cr.get(key) or "").strip()]
    start, end = parse_time((cr.get("window") or {}).get("start")), parse_time((cr.get("window") or {}).get("end"))
    window = (start, end) if start and end and start < end else None
    if not window:
        missing.append("jadwal implementasi (mulai < selesai, ISO-8601 dengan zona waktu)")
    checks.append(_check("FIELDS", "NEEDS_INFO" if missing else "PASS", "Kelengkapan change request",
                         ("Belum diisi: %s." % "; ".join(missing)) if missing else "Semua field wajib terisi.",
                         "sop", ctx.cites("sop14.fields", "ctrl12.fields")))

    if cr.get("type") == "access":
        access = cr.get("access") or {}
        gaps = [label for key, label in ACCESS_FIELDS if not str(access.get(key) or "").strip()]
        expires = access.get("expires_at")
        if expires and not _parse_date(expires):
            gaps.append("tanggal kedaluwarsa tidak valid (YYYY-MM-DD)")
        checks.append(_check("ACCESS", "NEEDS_INFO" if gaps else "PASS", "Syarat pemberian akses",
                             ("Belum diisi: %s." % "; ".join(gaps)) if gaps
                             else "Penerima, role pemberi otorisasi, dan kedaluwarsa %s tercatat." % expires,
                             "sop", ctx.cites("ctrl01.access")))

    # --- instruksi tersembunyi di teks ---------------------------------------
    text = "\n".join(str(cr.get(k) or "") for k in FREE_TEXT)
    injection = guard.detect_injection(text, scope="query")
    if injection["action"] in ("BLOCK", "WARN"):
        checks.append(_check("INJECTION", "WARN", "Instruksi ke sistem di dalam teks",
                             "Teks permintaan memuat kalimat yang ditujukan ke sistem/AI. Kalimat itu "
                             "diabaikan; keputusan di bawah hanya dari aturan.", "sistem"))

    # --- larangan eksposur internet ----------------------------------------
    if cr.get("exposure") == "internet":
        for a in assets:
            if a.get("zone") in SENSITIVE_ZONES:
                keys = ["ctrl09.exposure", "topo.%s" % a["zone"]]
                checks.append(_check("EXPOSURE", "BLOCK", "Eksposur internet dilarang",
                                     "%s ada di segmen %s yang tidak boleh diekspos langsung ke internet."
                                     % (a["asset_id"], a["zone"]), "sop", ctx.cites(*keys)))

    # --- risiko -------------------------------------------------------------
    level, reasons = classify_risk(cr, assets, window, ctx)
    checks.append(_check("RISK", "INFO", "Klasifikasi risiko: %s" % level,
                         "; ".join("%s: %s" % (r["level"], r["criterion"]) for r in reasons),
                         "sop" if all(r["basis"] == "sop" for r in reasons) else "interpretasi",
                         [c for r in reasons for c in r["citations"]]))

    # --- jendela waktu --------------------------------------------------------
    if window:
        wib = kb_facts.tz("WIB")
        if WMS_ASSETS & set(asset_ids):
            hit = daily_overlap(start, end, wib, (23, 0), (2, 0))
            if hit:
                extra_cab.append("sop7.cab")
                checks.append(_check("WMS-WINDOW", "WARN", "Bentrok jendela replikasi WMS",
                                     "Jadwal beririsan dengan replikasi %s. Geser jadwal, atau perubahan "
                                     "ini wajib diputuskan CAB." % fmt(hit[0], "WIB"), "sop",
                                     ctx.cites("wms.schedule", "wms.avoid", "sop7.cab")))
            else:
                checks.append(_check("WMS-WINDOW", "PASS", "Jendela replikasi WMS",
                                     "Tidak beririsan dengan replikasi 23:00-02:00 WIB.", "sop",
                                     ctx.cites("wms.schedule")))
        for site in sorted({a.get("site") for a in assets if a.get("site") in PRAYER}):
            frm, to = PRAYER[site]
            hit = daily_overlap(start, end, kb_facts.site_tz(site), frm, to, {4})
            if hit:
                checks.append(_check("FRIDAY-PRAYER", "WARN", "Bentrok shalat Jumat (%s)" % site,
                                     "Jadwal beririsan dengan %s; kantor %s tutup." % (fmt(hit[0]), site),
                                     "sop", ctx.cites("prayer.%s" % site, "prayer.flag")))
        branch_fw = [a for a in assets if a.get("type") == "Firewall" and a.get("site") != "Jakarta"]
        for a in branch_fw:
            local = kb_facts.site_tz(a["site"])
            if not inside_daily(start, end, local, (21, 0), (6, 0), WEEKDAYS):
                checks.append(_check("BRANCH-FW-WINDOW", "WARN" if emergency else "FAIL",
                                     "Di luar jendela maintenance firewall cabang",
                                     "%s hanya boleh dikerjakan Senin-Jumat 21:00-06:00 waktu %s%s."
                                     % (a["asset_id"], a["site"],
                                        "; emergency wajib persetujuan lisan IT Admin + ops manager"
                                        if emergency else ""), "interpretasi", ctx.cites("sop7.window")))
            else:
                checks.append(_check("BRANCH-FW-WINDOW", "PASS", "Jendela maintenance firewall cabang",
                                     "Seluruh jadwal di dalam jendela Senin-Jumat 21:00-06:00 waktu %s."
                                     % a["site"], "interpretasi", ctx.cites("sop7.window")))

    # --- memo 1 Oktober: firewall cabang wajib CAB tertulis + MFA -------------
    if any(a.get("type") == "Firewall" and a.get("site") != "Jakarta" for a in assets):
        try:
            memo = ctx.cites("memo.cab", "memo.mfa")
        except kb_facts.CitationError:
            memo = []
        keys = ctx.cites("sop7.verbal", "cmdb.fw-mks.mfa") + memo
        if memo:
            extra_cab.append("memo.cab")
        checks.append(_check("BRANCH-FW-MEMO", "WARN", "SOP-7 sudah digantikan memo 1 Okt 2026",
                             "SOP-7 masih mengizinkan persetujuan lisan, tetapi memo IT 1 Okt 2026 (lebih baru) "
                             "mewajibkan persetujuan CAB tertulis dan akses lewat jump-host + MFA. Yang dipakai: memo."
                             if memo else "Akses remote wajib lewat jump-host + MFA (CMDB).",
                             "sop", keys))

    # --- persetujuan -----------------------------------------------------------
    slots = approval_slots(level, assets, cr, ctx)
    cab_meeting = None
    if emergency:
        checks.append(_check("EMERGENCY", "WARN", "Emergency change",
                             "CAB dilewati. Wajib persetujuan lisan IT Admin dan system owner, lalu review "
                             "retroaktif CAB paling lambat 48 jam setelah eksekusi.", "sop",
                             ctx.cites("sop14.emergency", "ctrl12.emergency")))
    else:
        if extra_cab and not any(s["slot"] == "cab" for s in slots):
            slots.append(cab_slot(ctx.person("HR Manager"), extra_cab, ctx))
        if any(s["slot"] == "cab" for s in slots):
            meeting = next_cab_meeting(submitted_at)
            cab_meeting = {"at": meeting.isoformat(), "label": fmt(meeting, "WIB")}
            if window and start < meeting:
                checks.append(_check("LEAD-TIME", "FAIL", "Jadwal mendahului rapat CAB",
                                     "Perlu keputusan CAB. Rapat terdekat yang memenuhi batas 48 jam: %s, "
                                     "sedangkan jadwal mulai %s. Mundurkan jadwal, atau ajukan sebagai "
                                     "emergency bila memang darurat." % (fmt(meeting, "WIB"), fmt(start)),
                                     "sop", ctx.cites("sop14.cab")))
            else:
                checks.append(_check("LEAD-TIME", "PASS", "Waktu pengajuan sebelum rapat CAB",
                                     "Diputuskan di rapat CAB %s." % fmt(meeting, "WIB"), "sop",
                                     ctx.cites("sop14.cab")))

    # --- pemisahan tugas (aturan sistem) ---------------------------------------
    requester = (cr.get("requester") or {}).get("user")
    for s in slots:
        if requester and s["assignee"] == requester:
            fallback = ctx.person("HR Manager") if s["slot"] != "cab_chair" else ctx.person("IT Admin")
            if fallback == requester:
                fallback = ctx.person("IT Admin")
            checks.append(_check("SOD", "WARN", "Pemohon tidak boleh menyetujui permintaannya sendiri",
                                 "Slot %s dialihkan dari %s ke %s." % (s["label"], requester, fallback),
                                 "sistem"))
            s["assignee"], s["reassigned_from"] = fallback, requester

    worst = max((STATUS_RANK[c["status"]] for c in checks), default=0)
    outcome = {4: "BLOCKED", 3: "NEEDS_INFO", 2: "NEEDS_REVISION"}.get(worst, "READY")
    cited = {c["doc_id"]: c.get("effective_date") for chk in checks for c in chk["citations"]}
    return {
        "engine": ENGINE,
        "evaluated_at": submitted_at.isoformat(),
        "outcome": outcome,
        "risk": {"level": level, "reasons": reasons},
        "checks": checks,
        "approvals": slots,
        "cab_meeting": cab_meeting,
        "retro_review_hours": 48 if emergency else None,
        "kb_versions": dict(sorted(cited.items())),
    }


def _parse_date(value):
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None
