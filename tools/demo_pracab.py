#!/usr/bin/env python3
"""Demo terpandu Pra-CAB lewat HTTP API (stdlib saja).

Butuh server yang berjalan dengan --demo (jam demo dipakai untuk "maju ke
rapat CAB"):

    python backend/api/server.py --static frontend/dist --demo
    python tools/demo_pracab.py                      # default http://127.0.0.1:8787
    python tools/demo_pracab.py --base http://127.0.0.1:8788

Alur: Ragil mengajukan upgrade firmware firewall Makassar -> precheck SOP-14
-> dispatch sebelum disetujui ditolak -> CAB belum rapat ditolak -> jam maju
ke rapat CAB -> Indah menyetujui -> dispatch ke mock tool -> undo -> verifikasi
audit log. Lalu satu contoh yang diblokir: SSH dari internet ke HR DB.
Semua CR yang dibuat tercatat di audit log server.
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

RAGIL, INDAH, ANDINI = "Ragil Wibowo", "Indah Permatasari", "Andini Pratama"
NOW = "2026-10-27T10:00:00+07:00"        # Selasa; rapat CAB terdekat yang sah: Rabu 4 Nov
AFTER_MEETING = "2026-11-04T15:00:00+07:00"

FIRMWARE = {
    "title": "Upgrade firmware FortiGate Makassar", "assets": ["fw-edge-mks-01"],
    "change_kind": "firmware_upgrade", "channel": "form",
    "description": "Upgrade FortiOS fw-edge-mks-01 ke versi terbaru",
    "reason": "Menutup CVE kritis", "impact": "Uplink Makassar putus sekitar 10 menit",
    "implementation_plan": "Backup config, upload image, reboot, verifikasi tunnel",
    "rollback_plan": "Boot ke image sebelumnya dan restore config",
    "window": {"start": "2026-11-05T21:30:00+08:00", "end": "2026-11-05T22:30:00+08:00"},
}
SSH_HR = {
    "title": "Buka SSH dari internet ke HR DB", "assets": ["db-hr-jkt-01"],
    "change_kind": "firewall_rule", "exposure": "internet", "ports": [22],
    "description": "NAT port 22 dari internet ke db-hr-jkt-01 untuk maintenance malam ini",
    "reason": "Vendor perlu akses", "impact": "-", "implementation_plan": "Tambah rule NAT",
    "rollback_plan": "Hapus rule NAT",
    "window": {"start": "2026-10-27T22:00:00+07:00", "end": "2026-10-27T23:00:00+07:00"},
}


class Api:
    def __init__(self, base):
        self.base = base.rstrip("/")

    def call(self, path, body=None, user=None):
        if user and body is None:
            path += "?user=" + urllib.parse.quote(user)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method="POST" if data else "GET")
        if data:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                return res.status, json.loads(res.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())


def step(n, text):
    print("\n[%d] %s" % (n, text))


def show_precheck(cr):
    pre = cr["precheck"]
    print("    state   : %s" % cr["state"])
    print("    outcome : %s   risiko: %s" % (pre["outcome"], pre["risk"]["level"]))
    for c in pre["checks"]:
        print("    %-10s %-17s %s  [%s]" % (c["status"], c["id"], c["detail"][:90], c["basis"]))
        for cit in c["citations"][:2]:
            print("               ↳ %s: \"%s\"" % (cit["doc_id"], cit["quote"][:80]))
    for s in cr["approvals"]:
        print("    approver: %-40s -> %s (%s)" % (s["label"], s["assignee"], s["mode"]))
    if pre["cab_meeting"]:
        print("    rapat CAB: %s" % pre["cab_meeting"]["label"])


def expect_error(status, body, label):
    if status < 400:
        sys.exit("    GAGAL: %s seharusnya ditolak, tapi diterima." % label)
    print("    ditolak (HTTP %d %s): %s" % (status, body["error"]["code"], body["error"]["message"]))


def main():
    ap = argparse.ArgumentParser(description="Demo terpandu Pra-CAB.")
    ap.add_argument("--base", default="http://127.0.0.1:8787", help="URL server SecuritySahabat")
    args = ap.parse_args()
    api = Api(args.base)

    try:
        status, _ = api.call("/api/demo/clock", {"now": NOW})
    except urllib.error.URLError as exc:
        sys.exit("Server tidak bisa dihubungi di %s (%s). Jalankan server dulu." % (args.base, exc.reason))
    if status == 404:
        sys.exit("Server belum memakai --demo. Jalankan: python backend/api/server.py --static frontend/dist --demo")
    print("Jam demo: %s (Selasa)" % NOW)

    step(1, "Ragil (Ops Manager Makassar) membuat change request")
    status, cr = api.call("/api/requests", {"user": RAGIL, "fields": FIRMWARE})
    cid = cr["id"]
    print("    %s dibuat, state=%s, tombol untuk Ragil: %s" % (cid, cr["state"], cr["allowed_actions"]))

    step(2, "Ragil mengajukan -> precheck SOP-14 (tanpa LLM)")
    _, cr = api.call("/api/requests/%s/submit" % cid, {"user": RAGIL})
    show_precheck(cr)

    step(3, "Ragil mencoba dispatch sebelum disetujui")
    expect_error(*api.call("/api/requests/%s/dispatch" % cid, {"user": RAGIL}), "dispatch")

    step(4, "Indah mencoba mencatat keputusan CAB sebelum rapat")
    expect_error(*api.call("/api/requests/%s/approve" % cid, {"user": INDAH, "slot": "cab"}), "approve")

    step(5, "Jam demo maju ke setelah rapat CAB: %s" % AFTER_MEETING)
    api.call("/api/demo/clock", {"now": AFTER_MEETING})
    _, cr = api.call("/api/requests/%s" % cid, user=INDAH)
    print("    tombol untuk Indah sekarang: %s" % cr["allowed_actions"])

    step(6, "Indah mengisi slot CAB dan slot HR Manager")
    api.call("/api/requests/%s/approve" % cid, {"user": INDAH, "slot": "cab", "note": "Disetujui rapat CAB"})
    _, cr = api.call("/api/requests/%s/approve" % cid, {"user": INDAH, "slot": "cab_chair"})
    print("    state=%s" % cr["state"])

    step(7, "Ragil dispatch -> mock tool (tidak ada yang benar-benar terkirim)")
    _, cr = api.call("/api/requests/%s/dispatch" % cid, {"user": RAGIL})
    for a in cr["dispatch"]["actions"]:
        print("    %-22s %s  %s" % (a["tool"], a["status"], a.get("title") or a.get("system") or ""))
        if a.get("warning"):
            print("               ⚠ %s" % a["warning"])
    print("    undo sampai: %s" % cr["dispatch"]["undo_until"])

    step(8, "Ragil membatalkan dalam 60 detik")
    _, cr = api.call("/api/requests/%s/undo" % cid, {"user": RAGIL})
    print("    state=%s" % cr["state"])

    step(9, "Riwayat %s dari audit log" % cid)
    _, audit = api.call("/api/requests/%s/audit" % cid, user=RAGIL)
    for r in audit["records"]:
        print("    #%-4s %-14s %-9s %-18s hash=%s…" % (r["seq"], r["stage"], r["actor"].split()[0],
                                                     r["state_to"], r["hash"][:12]))

    step(10, "Contoh lain: Andini minta buka SSH dari internet ke HR DB")
    api.call("/api/demo/clock", {"now": NOW})
    _, other = api.call("/api/requests", {"user": ANDINI, "fields": SSH_HR})
    _, other = api.call("/api/requests/%s/submit" % other["id"], {"user": ANDINI})
    pre = other["precheck"]
    print("    state=%s outcome=%s risiko=%s" % (other["state"], pre["outcome"], pre["risk"]["level"]))
    for c in pre["checks"]:
        if c["id"] == "EXPOSURE":
            print("    %s: %s" % (c["status"], c["detail"]))

    step(11, "Verifikasi rantai hash audit log")
    _, verify = api.call("/api/audit/verify")
    print("    %s" % json.dumps(verify, ensure_ascii=False))

    api.call("/api/demo/clock", {"now": None})
    print("\nSelesai. Jam demo dikembalikan ke waktu nyata.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
