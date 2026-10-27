---
doc_id: "TOPO-HR-DATA"
title: "HR Database Segregation (MANDATORY)"
type: "topology"
owner: "Andini Pratama (IT Admin)"
status: "active"
effective_date: "2026-09-15"
tags: [hr-data, db-hr-jkt-01, vlan 99, segregation, internet exposure]
source: "topology.md [TOPO-NLP-001]"
source_ref: "§2.1"
restricted: false
zone: "common"
risk_level: "critical"

---

## HR Database Segregation (MANDATORY)

The HR database (db-hr-jkt-01) resides on VLAN 99 (hr-data). This is a **segregated VLAN** with the following hard rules:

- Only the HR application and backup server (backup-jkt-01) may connect to hr-data.
- NO direct internet exposure of any hr-data asset is permitted under any circumstances.
- Any change request proposing internet-facing access to hr-data must be classified as CRITICAL risk.
- Firewall rules between hr-data and all other segments are default-deny except explicitly approved flows.
