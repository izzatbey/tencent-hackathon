---
doc_id: "CTRL-06"
title: "A.8.13 Information backup"
type: "control"
iso: "A.8.13"
nist: "RC.RP-01"
owner: "Citra Kusuma (SOC Analyst)"
status: "active"
effective_date: "2026-08-01"
tags: [backup, restore, verification]
conflict_hint: "CTRL-06 mewajibkan verifikasi backup, tetapi menunjuk ke SOP-9 untuk jadwalnya. SOP-9 (bulanan) dan TOPO-BACKUP (menyebut pembaruan Oktober) tidak konsisten - lihat flag konflik."
source: "controls.md [CTRL-NLP-001]"
source_ref: "[CTRL-06]"
restricted: false
zone: "common"
risk_level: "medium"

---

## A.8.13 Information backup

Backup copies of information, software, and system images shall be maintained and tested regularly.

Guidance: backup schedules must be documented. Backups must be tested for restoration at the documented frequency. Backup integrity verification is mandatory — see SOP-9 for current verification schedule.
