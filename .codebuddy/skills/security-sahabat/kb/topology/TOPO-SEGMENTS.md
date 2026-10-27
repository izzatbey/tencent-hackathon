---
doc_id: "TOPO-SEGMENTS"
title: "Network Segments"
type: "topology"
owner: "Andini Pratama (IT Admin)"
status: "active"
effective_date: "2026-09-15"
tags: [segment, vlan, jakarta, makassar, jayapura, dmz]
source: "topology.md [TOPO-NLP-001]"
source_ref: "1. Network Segments"
restricted: false
zone: "common"
risk_level: "medium"

---

## Network Segments

PT NLP has the following network segments across its offices:

### 1.1 Jakarta HQ (WIB)

| Segment ID | Name | VLAN | Purpose | Internet Access |
|---|---|---|---|---|
| corp-jkt | Corporate Network | VLAN 10 | Staff workstations, printers, Wi-Fi | Yes (filtered via fw-edge-jkt-01) |
| dmz-jkt | DMZ | VLAN 20 | External-facing services (mail relay, reverse proxy) | Yes (restricted) |
| server-farm-jkt | Server Farm | VLAN 30 | Production servers (ERP, DB, K8s) | No direct exposure. Behind reverse proxy. |
| hr-data | HR Data VLAN | VLAN 99 | HR database only. Segregated. | No. Direct internet exposure PROHIBITED. |
| mgmt | Management Network | VLAN 40 | Monitoring, backup, admin access | No. Jump-host access only. |

### 1.2 Makassar Branch (WITA)

| Segment ID | Name | VLAN | Purpose | Notes |
|---|---|---|---|---|
| branch-mks | Branch Network | VLAN 50 | All Makassar devices | Single uplink to Jakarta via site-to-site VPN through fw-edge-mks-01. No redundancy. |

### 1.3 Jayapura Branch (WIT)

Jayapura branch has a basic internet connection (no VPN tunnel to Jakarta). Staff use cloud-based tools. No on-premise servers.
