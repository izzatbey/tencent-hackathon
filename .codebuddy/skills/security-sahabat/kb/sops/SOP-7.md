---
doc_id: "SOP-7"
title: "Remote Maintenance of Branch Firewalls"
type: "sop"
owner: "Andini Pratama (IT Admin)"
approved_by: "Indah Permatasari (HR Manager, acting CAB chair)"
status: "active"
version: "1.2"
effective_date: "2026-03-15"
conflict_hint: "SOP-7 membolehkan persetujuan LISAN untuk maintenance rutin firewall cabang, sementara CTRL-12 mewajibkan semua perubahan produksi lewat CAB. Untuk change request formal tetap pakai SOP-14; persetujuan lisan hanya untuk maintenance rutin di jendela yang diizinkan."
tags: [sop, remote maintenance of branch firewalls]
source: "sops.md [SOP-NLP-MAIN]"
source_ref: "SOP-7 v1.2"
redacted: false
restricted: false
zone: "common"
risk_level: "high"

---

### Purpose
This SOP governs remote maintenance activities on branch office firewalls, specifically fw-edge-mks-01 (Makassar) and any future branch firewalls.

### Scope
Applies to all IT staff and contractors performing remote maintenance on branch network infrastructure.

### Procedure

1. **Permitted time window:** Remote maintenance of branch firewalls is allowed any weekday (Monday–Friday) between 21:00 and 06:00 local branch time.
2. **Authorization:** Verbal approval from the on-call IT admin or ops manager is sufficient for routine maintenance (firmware updates, rule reviews, log cleanup).
3. **Access method:** SSH access via VPN to the branch firewall management interface.
4. **Change logging:** All changes must be logged in the IT change register within 24 hours of completion.
5. **Rollback plan:** A rollback plan must be prepared before commencing maintenance (e.g., previous firmware image, current rule set backup).
6. **Notification:** Notify the branch coordinator (Hendra Wijaya for Makassar) by phone before commencing maintenance.

### Exceptions
- Emergency maintenance outside the permitted window requires verbal approval from both the IT Admin and the branch ops manager.
- CAB approval is required for changes that affect the replication window (23:00–02:00 WIB).
