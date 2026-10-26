# Compliance Catalog — ISO 27001:2022 ↔ NIST CSF 2.0

> **Document ID:** CTRL-NLP-001
> **Last updated:** 2026-08-01
> **Owner:** Citra Kusuma (SOC Analyst)
> **Classification:** Internal — IT Department
> **Note:** This is a simplified ISO↔NIST mapping for assessment purposes. Full mappings are more complex.

---

[CTRL-01] ISO 27001:2022 A.5.15 Access control | NIST CSF 2.0 PR.AA-01
Access to information and other associated assets shall be provisioned, reviewed, modified and removed in accordance with the organization's access control topic-specific policy.
Guidance for change requests: any change granting new network or system access must name the requester, the authorizing role, and an expiry date. Temporary access must be reviewed and revoked after expiry.

[CTRL-02] ISO 27001:2022 A.5.18 Access rights | NIST CSF 2.0 PR.AA-05
Access to information and other associated assets shall be subject to a documented need-to-know principle and least privilege principle.
Guidance: users should only have access to information necessary for their role. Any access request must justify the business need. Role-based access control (RBAC) is the preferred model.

[CTRL-03] ISO 27001:2022 A.8.2 Privileged access rights | NIST CSF 2.0 PR.AA-05
Privileged access rights shall be restricted and managed through a formal authorization process.
Guidance: administrative/root access must use dedicated privileged accounts, not shared with regular accounts. Privileged access requires MFA. Emergency privileged access must be logged and reviewed within 24 hours.

[CTRL-04] ISO 27001:2022 A.8.5 Secure authentication | NIST CSF 2.0 PR.AA-03
Passwords shall be protected through secure authentication processes.
Guidance: password policy minimum requirements — minimum 12 characters, complexity (upper, lower, digit, special), rotation every 90 days, no password reuse for last 5 cycles, MFA required for all privileged accounts and remote access. Passwords must not be shared via chat or email.

[CTRL-05] ISO 27001:2022 A.8.9 Configuration management | NIST CSF 2.0 PR.PS-01
Hardware, software, network, and service configurations shall be established, documented, implemented, monitored, and reviewed.
Guidance: any configuration change to production systems (firewalls, switches, servers) must follow change management process. Default configurations must be reviewed and hardened. Unnecessary services must be disabled.

[CTRL-06] ISO 27001:2022 A.8.13 Information backup | NIST CSF 2.0 RC.RP-01
Backup copies of information, software, and system images shall be maintained and tested regularly.
Guidance: backup schedules must be documented. Backups must be tested for restoration at the documented frequency. Backup integrity verification is mandatory — see SOP-9 for current verification schedule.

[CTRL-07] ISO 27001:2022 A.8.16 Monitoring activities | NIST CSF 2.0 DE.CM-01
Networks, systems, and applications shall be monitored for security events.
Guidance: logging must be enabled on all critical systems. Logs must be sent to monitoring server (mon-jkt-01). Any change that disables or weakens monitoring is classified as HIGH risk minimum. SOC team reviews alerts during business hours and on-call after hours.

[CTRL-08] ISO 27001:2022 A.8.19 Installation of software on operational systems | NIST CSF 2.0 PR.PS-02
Procedures shall be implemented to verify the integrity of software installed on operational systems and to manage software installation on operational systems.
Guidance: no unapproved software may be installed on company laptops or servers. Software installation requires IT approval. Free or open-source software from the internet must be security-reviewed before installation. Unverified downloads are prohibited on corporate devices.

[CTRL-09] ISO 27001:2022 A.8.20 Networks security | NIST CSF 2.0 PR.IR-01
Networks and network devices shall be secured, managed, and controlled to protect information in systems and applications.
Guidance: direct internet exposure of internal databases or servers is prohibited. Firewall rule changes must follow change management. Port forwarding or NAT rules exposing internal services to the internet must be classified as HIGH or CRITICAL risk. SSH (port 22) from the internet to any internal server is classified as CRITICAL risk — requires jump-host with MFA.

[CTRL-10] ISO 27001:2022 A.8.22 Segregation of networks | NIST CSF 2.0 PR.IR-01
Groups of information services, users, and information systems shall be segregated from each other on networks.
Guidance: sensitive networks (hr-data, mgmt) must remain segregated. Any change that creates a bridge between hr-data and other segments must be classified as CRITICAL risk. Inter-VLAN routing changes require CAB approval. Default-deny between restricted VLANs and all other segments.

[CTRL-11] ISO 27001:2022 A.8.24 Use of cryptography | NIST CSF 2.0 PR.DS-02
Cryptographic keys shall be subject to a lifecycle management process.
Guidance: encryption in transit (TLS 1.2+) is mandatory for all external communications. Encryption at rest is required for databases containing personal data (HR DB). VPN tunnels must use AES-256 or equivalent. Key rotation schedule must be documented.

[CTRL-12] ISO 27001:2022 A.8.32 Change management | NIST CSF 2.0 PR.PS-01
Changes to information processing facilities shall be subject to formal change management procedures.
Guidance: all changes to production systems, network configurations, and security controls must go through the Change Advisory Board (CAB). Emergency changes may bypass CAB but must be retroactively reviewed within 48 hours. Change requests must document: what, why, impact assessment, rollback plan, and approver.

[CTRL-13] ISO 27001:2022 A.5.30 ICT readiness for business continuity | NIST CSF 2.0 RC.RP-01
The organization shall verify that ICT is ready for business continuity by conducting readiness tests.
Guidance: disaster recovery procedures must be documented and tested. Single points of failure must be identified and documented. The Makassar branch single uplink is a known SPOF — changes to this link must include continuity planning.

[CTRL-14] ISO 27001:2022 A.8.8 Management of technical vulnerabilities | NIST CSF 2.0 ID.RA-01
Technical vulnerability management shall be implemented to identify, assess, and remediate vulnerabilities.
Guidance: firmware and software must be kept up to date. Vulnerability scanning should be performed regularly. Critical vulnerabilities (CVSS 9+) must be patched within 7 days. Firmware upgrades on network devices must be tested in a staging environment before production deployment. If no staging environment exists, a maintenance window and rollback plan are mandatory.

---

*End of compliance catalog. For operational SOPs and policies, see sops.md. For network infrastructure context, see topology.md.*
