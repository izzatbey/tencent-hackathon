# Network Topology & Infrastructure — PT Nusantara Logistik Prima (NLP)

> **Document ID:** TOPO-NLP-001
> **Last updated:** 2026-09-15
> **Owner:** Andini Pratama (IT Admin)
> **Classification:** Internal — IT Department

---

## 1. Network Segments

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

---

## 2. Critical Infrastructure Rules

### 2.1 HR Database Segregation (MANDATORY)

The HR database (db-hr-jkt-01) resides on VLAN 99 (hr-data). This is a **segregated VLAN** with the following hard rules:

- Only the HR application and backup server (backup-jkt-01) may connect to hr-data.
- NO direct internet exposure of any hr-data asset is permitted under any circumstances.
- Any change request proposing internet-facing access to hr-data must be classified as CRITICAL risk.
- Firewall rules between hr-data and all other segments are default-deny except explicitly approved flows.

### 2.2 Server Farm Protection

- Production servers in server-farm-jkt have no direct internet access.
- External access routes through the DMZ reverse proxy only.
- Changes to server-farm firewall rules require CAB approval.

### 2.3 Makassar Branch — Single Uplink

- The Makassar branch has a single internet uplink through fw-edge-mks-01.
- There is NO redundancy. If the uplink fails, all Makassar operations (including WMS) go offline.
- Blast radius of any fw-edge-mks-01 change = entire Makassar branch.
- UPS generator is present but provides ~30 minutes of runtime.

---

## 3. Maintenance Windows & Schedules

### 3.1 WMS Replication Window

The Makassar Warehouse Management System (wms-mks-01) replicates to Jakarta nightly:

- **Schedule:** 23:00 WIB – 02:00 WIB (daily)
- **Impact:** WMS performance degraded during replication. Any network change affecting the branch-mks ↔ server-farm-jkt VPN tunnel during this window may cause replication failure and data inconsistency.
- **Recommendation:** Avoid scheduling network changes on fw-edge-mks-01 or vpn-gw-jkt-01 during this window.

### 3.2 Backup Schedule

- **Daily incremental:** 02:00 WIB (backup-jkt-01)
- **Weekly full:** Sunday 02:00 WIB
- **Verification:** See SOP-9 (note: verification frequency was updated — see chat exports for October ops memo)

### 3.3 Friday Prayer Times

Friday prayer (Salat Jumat) affects office availability:

- **Jakarta (WIB):** 11:30 – 13:00 WIB — offices closed, no meetings should be scheduled
- **Makassar (WITA):** 11:00 – 12:30 WITA — offices closed, no meetings should be scheduled
- Any change request or meeting proposed during these windows should be flagged.

### 3.4 Office Hours

- Jakarta HQ: 08:00 – 17:00 WIB
- Makassar Branch: 08:00 – 17:00 WITA (1 hour behind Jakarta)
- Jayapura Branch: 07:30 – 16:30 WIT (2 hours behind Jakarta)

---

## 4. Remote Access Policy (Infrastructure Context)

Remote access to infrastructure is controlled through:

- VPN Gateway (vpn-gw-jkt-01) for staff remote access
- Jump-host in mgmt VLAN for admin access to servers and firewalls
- MFA required for all administrative access (see SOP-7 and October IT memo for policy details)

---

## 5. Asset Dependencies (Blast Radius)

| Asset | Depends On | If This Asset Fails... |
|---|---|---|
| fw-edge-mks-01 | vpn-gw-jkt-01 (uplink) | Entire Makassar branch offline. WMS replication stops. |
| db-hr-jkt-01 | core-sw-jkt-01 (connectivity), backup-jkt-01 (backup) | HR operations halt. Personal data at risk if not isolated. |
| app-erp-prod | db-erp-jkt-01, core-sw-jkt-01 | Production ERP unavailable. Orders, inventory, finance impacted. |
| wms-mks-01 | fw-edge-mks-01, vpn-gw-jkt-01 | Warehouse operations halt. Replication to Jakarta at risk. |
| vpn-gw-jkt-01 | fw-edge-jkt-01 | All remote access and Makassar VPN tunnel down. |

---

## 6. Proyek Garuda (RESTRICTED — Infrastructure Note)

> **NOTE:** This section exists for infrastructure planning purposes only. Access to this project's details is restricted. Only personas with `proyek-garuda` in their `allowed_projects` may see any information about it.

Proyek Garuda is a confidential fleet-acquisition plan involving new warehouse capacity in Makassar. Infrastructure implications include a planned network expansion in the branch-mks segment. Details are available only to authorized personnel (IT Admin and HR Manager).

---

*End of topology document. For compliance requirements, see controls.md. For operational SOPs, see sops.md.*
