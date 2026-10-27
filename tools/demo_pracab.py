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
audit log. Lalu tiga contoh akses: SSH dari internet ke HR DB (diblokir),
akses ERP untuk Marketing (diblokir oleh policy register), dan akses aset
tanpa policy internal (dinilai dengan standar global, owner ikut menyetujui).
Terakhir policy register: memo baru -> aturan diusulkan -> disahkan pemilik
memo -> permintaan berikutnya berubah, permintaan lama tetap.

    python tools/demo_pracab.py --llm   # langkah 13 diekstrak LLM (SECURITY_SAHABAT_LLM=claude)
Semua CR yang dibuat tercatat di audit log server.
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

RAGIL, INDAH, ANDINI, EKA, CITRA = ("Ragil Wibowo", "Indah Permatasari", "Andini Pratama", "Eka Putri",
                                    "Citra Kusuma")
MEMO_QUOTE = "mail relay mail-jkt-01 hanya boleh diakses oleh tim IT"
MEMO = ("Memo IT Security, 27 Okt 2026. Mulai hari ini %s. Departemen lain memakai email cloud. "
        "Hubungi Citra Kusuma bila ada pertanyaan." % MEMO_QUOTE)
MEMO_RULE = {
    "title": "Mail relay hanya untuk IT", "topic": "access_scope", "check_id": "ACCESS-SCOPE",
    "tier": "perusahaan", "subject": {"asset": "mail-jkt-01"}, "action": "access",
    "condition": {"grantee_department_not_in": ["IT"]}, "effect": "BLOCK",
    "message": "{grantee} ({department}) tidak boleh mengakses {asset} (policy: {allowed}).",
    "pass_message": "{grantee} ({department}) boleh mengakses {asset}.",
    "sources": [{"type": "submitted", "quote": MEMO_QUOTE}], "owner": CITRA,
}
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
# "Tolong kepada bagian infrastruktur, untuk pihak marketing diberikan akses VPN ke server A"
ACCESS = {
    "type": "access", "change_kind": "access_grant", "title": "Akses VPN ke ERP untuk Marketing",
    "description": "Tolong bagian infrastruktur memberi tim marketing akses VPN ke app-erp-prod",
    "reason": "Kampanye Q4 perlu data stok", "impact": "Akun VPN baru", "implementation_plan": "Buat akun VPN + grup akses",
    "rollback_plan": "Cabut akun",
    "access": {"grantee": "Lina Kartika", "authorizing_role": "Team Lead", "expires_at": "2026-12-31"},
    "window": {"start": "2026-11-09T10:00:00+07:00", "end": "2026-11-09T11:00:00+07:00"},
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


def show_scope(cr):
    pre = cr["precheck"]
    print("    state=%s outcome=%s risiko=%s" % (cr["state"], pre["outcome"], pre["risk"]["level"]))
    for c in pre["checks"]:
        if c["id"] == "ACCESS-SCOPE":
            print("    %s [%s]: %s" % (c["status"], c["basis"], c["detail"]))
            for cit in c["citations"]:
                print("               ↳ %s: \"%s\"" % (cit["doc_id"], cit["quote"][:80]))


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
    ap.add_argument("--llm", action="store_true",
                    help="Langkah 13 memakai /api/policies/extract (server harus SECURITY_SAHABAT_LLM=claude)")
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

    step(11, "Contoh \"Server A\": Eka (Team Lead) minta akses app-erp-prod untuk Lina (Marketing)")
    _, acc = api.call("/api/requests", {"user": EKA, "fields": dict(ACCESS, assets=["app-erp-prod"])})
    _, acc = api.call("/api/requests/%s/submit" % acc["id"], {"user": EKA})
    show_scope(acc)

    step(12, "Aset tanpa policy internal: akses mail-jkt-01 untuk Lina -> dinilai dengan standar global")
    _, acc = api.call("/api/requests", {"user": EKA, "fields": dict(ACCESS, assets=["mail-jkt-01"],
                                                                   title="Akses mail relay untuk Marketing")})
    _, acc = api.call("/api/requests/%s/submit" % acc["id"], {"user": EKA})
    show_scope(acc)
    for s in acc["approvals"]:
        print("    approver: %-32s -> %s" % (s["label"], s["assignee"]))

    first_mail = acc

    step(13, "Policy register: Andini mengajukan aturan dari memo Citra (%s)"
         % ("diekstrak LLM" if args.llm else "diisi manual"))
    if args.llm:
        status, out = api.call("/api/policies/extract", {"user": ANDINI, "title": "Memo mail relay",
                                                         "text": MEMO, "owner": CITRA})
        if status != 200:
            sys.exit("    ekstraksi gagal (HTTP %d %s): %s" % (status, out["error"]["code"], out["error"]["message"]))
        for d in out["dropped"]:
            print("    dibuang: %s (%s)" % (d.get("title"), d["reason"]))
        if not out["proposed"]:
            sys.exit("    LLM tidak mengusulkan aturan yang lolos verifikasi.")
        rule = out["proposed"][0]
        print("    diusulkan oleh %s/%s" % (out["llm"]["provider"], out["llm"]["model"]))
    else:
        _, rule = api.call("/api/policies", {"user": ANDINI, "rule": MEMO_RULE,
                                             "source": {"title": "Memo mail relay", "text": MEMO, "owner": CITRA}})
    print("    %s [%s] %s" % (rule["id"], rule["status"], rule["title"]))
    print("    kondisi: %s -> %s" % (json.dumps(rule["condition"]), rule["effect"]))
    print("    kutipan: \"%s\"" % rule["sources"][0]["quote"])
    print("    pemilik dokumen: %s · tombol untuk Andini: %s" % (rule["owner"], rule["allowed_actions"]))

    step(14, "Yang tidak berhak mencoba mengesahkan, lalu Citra (pemilik memo) mengesahkan")
    expect_error(*api.call("/api/policies/%s/approve" % rule["id"], {"user": EKA}), "approve oleh Eka")
    expect_error(*api.call("/api/policies/%s/approve" % rule["id"], {"user": ANDINI}), "approve oleh pengusul")
    _, rule = api.call("/api/policies/%s/approve" % rule["id"], {"user": CITRA})
    print("    %s sekarang %s, berlaku mulai %s" % (rule["id"], rule["status"], rule["effective_date"]))

    step(15, "Lina mengajukan akses mail-jkt-01 lagi -> keputusan mengikuti aturan baru")
    _, acc = api.call("/api/requests", {"user": EKA, "fields": dict(ACCESS, assets=["mail-jkt-01"],
                                                                   title="Akses mail relay untuk Marketing")})
    _, acc = api.call("/api/requests/%s/submit" % acc["id"], {"user": EKA})
    show_scope(acc)
    _, old = api.call("/api/requests/%s" % first_mail["id"], user=EKA)
    print("    permintaan sebelumnya (%s) tetap: %s, %s" % (old["id"], old["state"],
                                                          old["precheck"]["outcome"]))

    step(16, "Verifikasi rantai hash audit log")
    _, verify = api.call("/api/audit/verify")
    print("    %s" % json.dumps(verify, ensure_ascii=False))

    api.call("/api/demo/clock", {"now": None})
    print("\nSelesai. Jam demo dikembalikan ke waktu nyata.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
