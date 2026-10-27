---
doc_id: "SOP-14"
title: "Change Management Process"
type: "sop"
owner: "Andini Pratama (IT Admin)"
approved_by: "Indah Permatasari (HR Manager, acting CAB chair)"
status: "active"
version: "2.0"
effective_date: "2026-03-01"
tags: [sop, change management process]
source: "sops.md [SOP-NLP-MAIN]"
source_ref: "SOP-14 v2.0"
redacted: false
restricted: false
zone: "common"
risk_level: "medium"

---

### Purpose
Defines the process for requesting, reviewing, and implementing changes to NLP's IT infrastructure.

### Scope
Applies to all changes to production systems, network configurations, security controls, and critical applications.

### Procedure

1. **Change request:** Submit via the IT change management system with: description, reason, impact assessment, implementation plan, rollback plan, and requested implementation time.
2. **CAB review:** The Change Advisory Board (CAB) meets weekly on Wednesdays 14:00 WIB. Requests must be submitted at least 48 hours before the CAB meeting.
3. **Emergency changes:** May bypass CAB but must be retroactively reviewed within 48 hours. Requires verbal approval from both the IT Admin and the system owner.
4. **Risk classification:**
   - LOW: No impact on production, reversible, off-hours
   - MEDIUM: Limited impact, recoverable, requires follow-up verification
   - HIGH: Touches sensitive zone, affects availability, or weakens security controls
   - CRITICAL: Exposes crown-jewel systems, removes authentication/backup, or is effectively irreversible
5. **Approval authority:**
   - LOW: IT Admin
   - MEDIUM: System owner + IT Admin
   - HIGH/CRITICAL: CAB + HR Manager (acting CAB chair)

### Reference
- ISO 27001 A.8.32 Change management [CTRL-12]
