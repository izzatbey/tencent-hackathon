---
doc_id: "CTRL-10"
title: "A.8.22 Segregation of networks"
type: "control"
iso: "A.8.22"
nist: "PR.IR-01"
owner: "Citra Kusuma (SOC Analyst)"
status: "active"
effective_date: "2026-08-01"
tags: [network, segmentation, vlan, hr-data, inter-vlan]
source: "controls.md [CTRL-NLP-001]"
source_ref: "[CTRL-10]"
restricted: false
zone: "common"
risk_level: "critical"

---

## A.8.22 Segregation of networks

Groups of information services, users, and information systems shall be segregated from each other on networks.

Guidance: sensitive networks (hr-data, mgmt) must remain segregated. Any change that creates a bridge between hr-data and other segments must be classified as CRITICAL risk. Inter-VLAN routing changes require CAB approval. Default-deny between restricted VLANs and all other segments.
