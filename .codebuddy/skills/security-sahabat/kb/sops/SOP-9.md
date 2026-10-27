---
doc_id: "SOP-9"
title: "Database Backup Verification"
type: "sop"
owner: "Andini Pratama (IT Admin)"
approved_by: "Indah Permatasari (HR Manager, acting CAB chair)"
status: "active"
version: "1.0"
effective_date: "2026-01-10"
topic: "backup-verification"
conflict_hint: "SOP-9 menetapkan verifikasi backup BULANAN, tetapi bagian Notes menyebut frekuensi sudah diperbarui setelah insiden April 2026 dan dokumen penggantinya TIDAK ADA di knowledge base. Jangan menebak frekuensi baru - jawab sesuai SOP-9 lalu minta konfirmasi owner."
tags: [sop, database backup verification]
source: "sops.md [SOP-NLP-MAIN]"
source_ref: "SOP-9 v1.0"
redacted: false
restricted: false
zone: "common"
risk_level: "medium"

---

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
