# Standard Operating Procedures — PT Nusantara Logistik Prima (NLP)

> **Document ID:** SOP-NLP-MAIN
> **Last updated:** 2026-03-15
> **Owner:** Andini Pratama (IT Admin)
> **Classification:** Internal — All Staff

---

## SOP-7: Remote Maintenance of Branch Firewalls

> **Status:** FORMAL DOCUMENT
> **Version:** 1.2
> **Effective date:** 2026-03-15
> **Author:** Andini Pratama (IT Admin)
> **Approved by:** Indah Permatasari (HR Manager, acting CAB chair)

### Purpose
This SOP governs remote maintenance activities on branch office firewalls, specifically fw-edge-mks-01 (Makassar) and any future branch firewalls.

### Scope
Applies to all IT staff and contractors performing remote maintenance on branch network infrastructure.

### Procedure

1. **Permitted time window:** Remote maintenance of branch firewalls is allowed any weekday (Monday–Friday) between 21:00 and 06:00 local branch time.
2. **Authorization:** Verbal approval from the on-call IT admin or ops manager is sufficient for routine maintenance (firmware updates, rule reviews, log cleanup).
3. **Access method:** SSH access via VPN to the branch firewall management interface.
4. **Change logging:** All changes must be logged in the IT change register within 24 hours of completion.
5. **Rollback plan:** A rollback plan must be prepared before commencing maintenance (e.g., previous firmware image, current rule set backup).
6. **Notification:** Notify the branch coordinator (Hendra Wijaya for Makassar) by phone before commencing maintenance.

### Exceptions
- Emergency maintenance outside the permitted window requires verbal approval from both the IT Admin and the branch ops manager.
- CAB approval is required for changes that affect the replication window (23:00–02:00 WIB).

---

## SOP-9: Database Backup Verification

> **Status:** FORMAL DOCUMENT
> **Version:** 1.0
> **Effective date:** 2026-01-10
> **Author:** Andini Pratama (IT Admin)
> **Approved by:** Indah Permatasari (HR Manager, acting CAB chair)

### Purpose
Defines the schedule and procedure for verifying database backup integrity.

### Scope
Applies to all production databases: db-hr-jkt-01, db-erp-jkt-01, and future production databases.

### Procedure

1. **Backup schedule:** Daily incremental at 02:00 WIB. Weekly full on Sunday at 02:00 WIB.
2. **Verification frequency:** Backup integrity verification (test restore) shall be performed **monthly** — on the first Saturday of each month.
3. **Verification scope:** A 10% random sample of tables from each database is restored to a test environment and checked for row count consistency and checksum match.
4. **Documentation:** Verification results are logged in the backup verification register (maintained by IT Admin).
5. **Failure handling:** If verification fails, the IT Admin must be notified immediately. Re-run the failed backup and escalate to CAB if the issue persists.

### Notes
- The April 2026 incident (corrupted backup of db-erp-jkt-01) highlighted the need for more frequent verification. See IT announcements for the updated frequency.

---

## SOP-12: Software Installation on Corporate Devices

> **Status:** FORMAL DOCUMENT
> **Version:** 1.1
> **Effective date:** 2026-02-20
> **Author:** Citra Kusuma (SOC Analyst)
> **Approved by:** Andini Pratama (IT Admin)

### Purpose
Governs the installation of software on company laptops, desktops, and servers.

### Scope
Applies to all employees, contractors, and visitors using NLP corporate devices.

### Procedure

1. **Approval required:** No software may be installed on corporate devices without prior IT approval. Submit a request to IT (andini.pratama@nlp.co.id) with the software name, source URL, and business justification.
2. **Free and open-source software:** Must be reviewed by the SOC team for known vulnerabilities and malware before installation. Download only from official sources or verified repositories.
3. **Prohibited software:** Pirated software, software from untrusted download sites, and software with known security issues are strictly prohibited.
4. **Server software:** Installation on production servers follows SOP-14 (Change Management) and requires CAB approval.
5. **Personal devices:** BYOD is not permitted for accessing internal systems. Only company-issued devices may connect to corp-jkt or server-farm-jkt.

### Reference
- ISO 27001 A.8.19 Installation of software on operational systems [CTRL-08]

---

## SOP-14: Change Management Process

> **Status:** FORMAL DOCUMENT
> **Version:** 2.0
> **Effective date:** 2026-03-01
> **Author:** Andini Pratama (IT Admin)
> **Approved by:** Indah Permatasari (HR Manager, acting CAB chair)

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

---

## SOP-15: External Data Sharing

> **Status:** FORMAL DOCUMENT
> **Version:** 1.0
> **Effective date:** 2026-03-10
> **Author:** Citra Kusuma (SOC Analyst)
> **Approved by:** Indah Permatasari (HR Manager, acting CAB chair)

### Purpose
Governs the sharing of company data with external parties (vendors, partners, clients).

### Scope
Applies to all employees sharing NLP data outside the organization.

### Procedure

1. **Classification:** Before sharing, classify the data as Public, Internal, Confidential, or Restricted.
2. **Restricted data (NIK, financial data, Proyek Garuda):** May NOT be shared externally without written approval from the HR Manager and IT Admin.
3. **Confidential data (operational data, SOPs):** May be shared with approved vendors only after signing an NDA. Approval from the system owner is required.
4. **External sharing tools:** Company-approved file sharing is via the corporate Google Workspace. Personal cloud storage (personal Google Drive, Dropbox, etc.) is prohibited for company data.
5. **PII protection:** All personal data (NIK, phone numbers, emails) must be masked when shared with external parties unless explicit consent is documented.

### Reference
- ISO 27001 A.5.15 Access control [CTRL-01]
- ISO 27001 A.8.24 Use of cryptography [CTRL-11]

---

*End of SOP document. For compliance catalog, see controls.md. For network infrastructure context, see topology.md.*
