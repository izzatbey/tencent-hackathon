---
doc_id: "TOPO-SERVER-FARM"
title: "Server Farm Protection"
type: "topology"
owner: "Andini Pratama (IT Admin)"
status: "active"
effective_date: "2026-09-15"
tags: [server-farm-jkt, reverse proxy, cab]
source: "topology.md [TOPO-NLP-001]"
source_ref: "§2.2"
restricted: false
zone: "common;it-admin"
risk_level: "high"

---

## Server Farm Protection

- Production servers in server-farm-jkt have no direct internet access.
- External access routes through the DMZ reverse proxy only.
- Changes to server-farm firewall rules require CAB approval.
