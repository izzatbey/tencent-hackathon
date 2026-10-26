---
doc_id: "TOPO-BLAST-RADIUS"
title: "Asset Dependencies (Blast Radius)"
type: "topology"
owner: "Andini Pratama (IT Admin)"
status: "active"
effective_date: "2026-09-15"
tags: [dependency, blast radius, db-hr-jkt-01, app-erp-prod]
source: "topology.md [TOPO-NLP-001]"
source_ref: "5. Asset Dependencies (Blast Radius)"
restricted: false
zone: "common;it-admin"
risk_level: "high"

---

## Asset Dependencies (Blast Radius)

| Asset | Depends On | If This Asset Fails... |
|---|---|---|
| fw-edge-mks-01 | vpn-gw-jkt-01 (uplink) | Entire Makassar branch offline. WMS replication stops. |
| db-hr-jkt-01 | core-sw-jkt-01 (connectivity), backup-jkt-01 (backup) | HR operations halt. Personal data at risk if not isolated. |
| app-erp-prod | db-erp-jkt-01, core-sw-jkt-01 | Production ERP unavailable. Orders, inventory, finance impacted. |
| wms-mks-01 | fw-edge-mks-01, vpn-gw-jkt-01 | Warehouse operations halt. Replication to Jakarta at risk. |
| vpn-gw-jkt-01 | fw-edge-jkt-01 | All remote access and Makassar VPN tunnel down. |
