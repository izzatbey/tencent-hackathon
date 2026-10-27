---
doc_id: "CTRL-11"
title: "A.8.24 Use of cryptography"
type: "control"
iso: "A.8.24"
nist: "PR.DS-02"
owner: "Citra Kusuma (SOC Analyst)"
status: "active"
effective_date: "2026-08-01"
tags: [cryptography, encryption, tls, vpn, key rotation]
source: "controls.md [CTRL-NLP-001]"
source_ref: "[CTRL-11]"
restricted: false
zone: "common"
risk_level: "medium"

---

## A.8.24 Use of cryptography

Cryptographic keys shall be subject to a lifecycle management process.

Guidance: encryption in transit (TLS 1.2+) is mandatory for all external communications. Encryption at rest is required for databases containing personal data (HR DB). VPN tunnels must use AES-256 or equivalent. Key rotation schedule must be documented.
