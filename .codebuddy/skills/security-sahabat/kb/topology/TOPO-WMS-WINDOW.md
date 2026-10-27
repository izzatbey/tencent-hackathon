---
doc_id: "TOPO-WMS-WINDOW"
title: "WMS Replication Window"
type: "topology"
owner: "Andini Pratama (IT Admin)"
status: "active"
effective_date: "2026-09-15"
tags: [wms-mks-01, replication, 23:00, maintenance window]
source: "topology.md [TOPO-NLP-001]"
source_ref: "§3.1"
restricted: false
zone: "common;warehouse"
risk_level: "medium"

---

## WMS Replication Window

The Makassar Warehouse Management System (wms-mks-01) replicates to Jakarta nightly:

- **Schedule:** 23:00 WIB – 02:00 WIB (daily)
- **Impact:** WMS performance degraded during replication. Any network change affecting the branch-mks ↔ server-farm-jkt VPN tunnel during this window may cause replication failure and data inconsistency.
- **Recommendation:** Avoid scheduling network changes on fw-edge-mks-01 or vpn-gw-jkt-01 during this window.
