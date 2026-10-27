---
doc_id: "CTRL-09"
title: "A.8.20 Networks security"
type: "control"
iso: "A.8.20"
nist: "PR.IR-01"
owner: "Citra Kusuma (SOC Analyst)"
status: "active"
effective_date: "2026-08-01"
tags: [network, firewall, ssh, port 22, nat, internet exposure]
source: "controls.md [CTRL-NLP-001]"
source_ref: "[CTRL-09]"
restricted: false
zone: "common"
risk_level: "critical"

---

## A.8.20 Networks security

Networks and network devices shall be secured, managed, and controlled to protect information in systems and applications.

Guidance: direct internet exposure of internal databases or servers is prohibited. Firewall rule changes must follow change management. Port forwarding or NAT rules exposing internal services to the internet must be classified as HIGH or CRITICAL risk. SSH (port 22) from the internet to any internal server is classified as CRITICAL risk — requires jump-host with MFA.
