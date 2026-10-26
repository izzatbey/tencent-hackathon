---
doc_id: "TOPO-MKS-UPLINK"
title: "Makassar Branch - Single Uplink"
type: "topology"
owner: "Andini Pratama (IT Admin)"
status: "active"
effective_date: "2026-09-15"
tags: [fw-edge-mks-01, branch-mks, uplink, redundancy, blast radius]
source: "topology.md [TOPO-NLP-001]"
source_ref: "§2.3"
restricted: false
zone: "common;ops-read"
risk_level: "medium"

---

## Makassar Branch - Single Uplink

- The Makassar branch has a single internet uplink through fw-edge-mks-01.
- There is NO redundancy. If the uplink fails, all Makassar operations (including WMS) go offline.
- Blast radius of any fw-edge-mks-01 change = entire Makassar branch.
- UPS generator is present but provides ~30 minutes of runtime.
