---
doc_id: "CTRL-14"
title: "A.8.8 Management of technical vulnerabilities"
type: "control"
iso: "A.8.8"
nist: "ID.RA-01"
owner: "Citra Kusuma (SOC Analyst)"
status: "active"
effective_date: "2026-08-01"
tags: [vulnerability, patching, cvss, firmware]
source: "controls.md [CTRL-NLP-001]"
source_ref: "[CTRL-14]"
restricted: false
zone: "common"
risk_level: "medium"

---

## A.8.8 Management of technical vulnerabilities

Technical vulnerability management shall be implemented to identify, assess, and remediate vulnerabilities.

Guidance: firmware and software must be kept up to date. Vulnerability scanning should be performed regularly. Critical vulnerabilities (CVSS 9+) must be patched within 7 days. Firmware upgrades on network devices must be tested in a staging environment before production deployment. If no staging environment exists, a maintenance window and rollback plan are mandatory.

*End of compliance catalog. For operational SOPs and policies, see sops.md. For network infrastructure context, see topology.md.*
