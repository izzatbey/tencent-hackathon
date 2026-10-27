---
doc_id: "TOPO-REMOTE-ACCESS"
title: "Remote Access Policy (Infrastructure Context)"
type: "topology"
owner: "Andini Pratama (IT Admin)"
status: "active"
effective_date: "2026-09-15"
tags: [vpn-gw-jkt-01, jump-host, mfa, remote access]
source: "topology.md [TOPO-NLP-001]"
source_ref: "4. Remote Access Policy (Infrastructure Context)"
restricted: false
zone: "common"
risk_level: "high"

---

## Remote Access Policy (Infrastructure Context)

Remote access to infrastructure is controlled through:

- VPN Gateway (vpn-gw-jkt-01) for staff remote access
- Jump-host in mgmt VLAN for admin access to servers and firewalls
- MFA required for all administrative access (see SOP-7 and October IT memo for policy details)
