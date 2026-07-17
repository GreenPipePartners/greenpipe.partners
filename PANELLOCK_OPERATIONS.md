# PanelLock Operating Policy

This is the implementation baseline for PanelLock. Customer-facing terms should be reviewed by qualified counsel before general availability.

## Conversion Inputs

The public source-platform matrix is implemented in `panellock/catalog.py`. A flat-fee conversion requires a restorable native project or documented exports sufficient to reproduce graphics, tags, alarms, navigation, and scripts. Custom controls, proprietary widgets, unavailable source, PLC changes, historian/database migration, third-party modules, travel, shipping, taxes, licensing not selected in the proposal, and production downtime are excluded unless a confirmed quote says otherwise.

FactoryTalk View ME customers must provide a restorable application, not an upload-only `.MER`. Vendor-tooling platforms require customer-authorized access to the applicable engineering software and exports. Acceptance testing must cover navigation, tag read/write authorization, alarms, trends/history, scripts, drivers, user roles, and agreed screen resolutions.

Browser-generated proposals are preliminary and cannot be accepted by purchase order. Final technical and commercial approval requires review of the source project, exports, dependencies, licenses, custom controls, communications, and supporting documentation to establish a reliable and supportable conversion path.

## Backup And Retention Defaults

- Primary Ignition artifact: native `.gwbk`, plus external database dumps, certificates, module/license inventory, and OS/configuration manifests where applicable.
- Included quota: 25 GiB per managed panel; alert at 80% and 95%.
- Maximum single upload: 10 GiB. Larger backups require a custom storage plan.
- Retention: 30 daily, 12 monthly, and 3 annual recovery points. Keep every pre-update backup at least 90 days.
- Immutability: object-lock daily copies for 30 days and monthly copies for their retention period.
- Integrity: hash every object, scan in quarantine, and fail closed if scanning is unavailable. Run a quarterly test restore and annual customer-observed recovery exercise.
- Residency: the organization selects US East or US West at onboarding. Customer artifacts and replicas remain in that region unless the customer approves a move.
- Termination: 30-day export window, followed by deletion of active and backup copies within 60 days unless a legal or incident hold applies.
- Support access: no standing backup access. Require named MFA accounts, a customer-approved ticket, logged just-in-time access, and automatic expiration within four hours. Break-glass access triggers immediate notice and next-business-day review.
- AI: opt-in per organization and task. Never train on customer projects, screenshots, logs, or backups. Redact credentials and production identifiers, minimize context, disable provider training, disclose subprocessors/region, and delete prompts/outputs within 30 days or use provider zero-retention mode.

## Subscription And Website Terms Checklist

- Separate Inductive Automation perpetual license fees from recurring PanelLock coverage. Identify Ignition as an Inductive Automation product and PanelLock as an independent service.
- State quote validity, currency, taxes, payment timing, renewal, cancellation, refund, suspension, data-export, storage, support hours, and overage terms.
- Define the license owner and activation-key custodian. State transfer obligations and service-termination treatment.
- PanelLock Protect includes two scheduled update reviews per year plus out-of-cycle response for applicable critical vulnerabilities. Emergency response requires an affected supported component and a tested vendor patch or documented mitigation; it does not guarantee uninterrupted operation or an unconditional repair deadline.
- PanelLock Protect uses source-available AgentLab infrastructure. Each service scope must identify qualified personnel responsible for its configuration and maintenance.
- Reserve approved maintenance windows and emergency security maintenance rights.
- Customer must provide accurate inventory, operational contacts, blackout periods, safe-state procedures, tested manual fallback, and a person with stop/go authority.
- Customer retains responsibility for process safety, regulatory compliance, alarm response, and authorization of control-affecting changes.
- Prohibit credential sharing, malware, unauthorized scanning, tenant-access attempts, safety bypasses, unsupported modules, and resource abuse.
- Address confidentiality, subprocessors, data ownership, region, breach notice, telemetry, AI handling, project IP, reusable PanelLock tooling, warranty disclaimers, liability caps, indemnity, export controls, governing law, and order of precedence among quote, SLA, DPA, and terms.
- Require explicit acknowledgement that updates may restart gateways, disconnect HMI sessions, interrupt alarms/history/device communications, require rollback, and cause production downtime despite testing.

## CISA Alignment Target

CISA does not issue a general-purpose "CISA compliant" certification for commercial HMI services. PanelLock can make a supportable alignment claim by defining a scoped control baseline, retaining evidence, and obtaining independent review.

- Map the service to applicable CISA Cross-Sector Cybersecurity Performance Goals, including asset inventory, vulnerability management, phishing-resistant MFA, protected backups, tested recovery, logging, incident response, and supply-chain controls.
- Monitor the CISA Known Exploited Vulnerabilities Catalog and applicable vendor advisories. Document applicability, exposure, compensating controls, test results, customer authorization, deployment, and closure.
- Define response targets by severity and exposure instead of promising that every disclosed vulnerability can be patched immediately. Unsupported products, unavailable vendor fixes, unsafe maintenance windows, and failed validation require a documented mitigation or risk decision.
- Use NIST Cybersecurity Framework 2.0 for governance and evidence organization. Use the applicable ISA/IEC 62443 requirements when customers need an independently assessable industrial-control security baseline.
- Describe the public claim as "aligned with applicable CISA guidance" until a named scope, control mapping, evidence package, and independent assessment support stronger language.

## Threat Model And Update Runbook

### AgentLab execution boundary

- The portal directs a reusable AgentLab service appliance. The panel PC does not run the PanelLock portal agent.
- The AgentLab reaches the portal through an independent outbound-only HTTPS uplink, such as Wi-Fi or a second Ethernet adapter.
- A separate Ethernet work interface connects directly to the selected panel PC for the authorized service session.
- Never bridge, route, forward, or NAT traffic between the portal uplink and panel-facing interface. Disable IP forwarding and automatic connection sharing before service work.
- Treat the AgentLab as a relatively untrusted execution endpoint: issue short-lived panel-bound credentials, deliver only signed allowlisted operations, keep no standing customer credentials, and clear customer artifacts when the service session ends.
- Require local safe-state confirmation, current backups, explicit stop/go authority, and a physical disconnect path before the AgentLab can perform mutating work.
- The production data model must keep panel-PC inventory, AgentLab cryptographic identity, and temporary AgentLab-to-panel service sessions as separate records. The current prototype `Device` model does not yet enforce that separation.

### Principal threats

- Stolen customer/staff/device credentials, replayed enrollment, spoofed MAC addresses, and compromised support endpoints.
- Malicious backups, unsigned modules, poisoned downloads, dependency incompatibility, configuration drift, backup tampering, unsafe control writes, insider misuse, and tenant data exposure.
- AI prompt injection or invalid output reaching an execution primitive.
- Update interruption, database migration failure, license fault, failed redundancy/failover, alarm loss, and rollback failure.

### Preventive controls

- Device-generated Ed25519 identity, one-use enrollment token, replay nonce, clock window, revocation, outbound HTTPS only, and explicit replacement assignment. MAC/serial values are inventory only.
- Tenant-scoped querysets, role checks, MFA for staff/owners, short support grants, append-only audit, private encrypted storage, quarantine scanning, short signed URLs, and immutable backups.
- Vendor-authenticated artifacts with recorded provenance and hashes. KMS signs a short-lived, device-bound manifest.
- Only schema-validated allowlisted operations. Never expose arbitrary shell/PowerShell. AI cannot sign, approve, or execute.

### Per-update runbook

1. Inventory Ignition, OS/JVM, modules, drivers, certificates, databases, devices, projects, redundancy, manual fallback, and safety impact.
2. Review release notes, advisories, known issues, compatibility, licensing, database migrations, and rollback support.
3. Restore the customer backup in isolation and test the exact version/module combination.
4. Verify login, navigation, authorized writes, alarms/acknowledgement, historian, audit log, reports, scripts, devices, databases, Vision/Perspective launch, and redundancy.
5. Capture a fresh encrypted backup, database backup, module/license inventory, checksums, and successful restore result.
6. Obtain customer window, operator contact, downtime acknowledgement, rollback authority, and stop/go approval; freeze unrelated changes.
7. Put the process in the agreed safe state and confirm local/manual control remains available.
8. Execute the immutable approved plan with just-in-time access and complete session/change logging.
9. Stop on unexpected PLC writes, alarm loss, device disconnect, migration error, license fault, failover instability, or performance outside the agreed threshold.
10. Run customer-observed smoke tests. Roll back binaries, configuration, and database state together when a trigger is met.
11. Monitor for one production cycle or 24 hours. Preserve logs, hashes, approvals, tests, and final inventory; revoke temporary access and rotate exposed secrets.

### Incident runbooks

- Lost/stolen device: revoke credential, mark device lost, preserve audit, enroll replacement with a new key, and explicitly reassign the logical panel.
- Malicious upload: quarantine, deny download/AI access, notify security and customer, preserve evidence under incident hold, and rotate credentials if the archive contained secrets.
- Tenant exposure: disable affected access paths, preserve logs, notify security/legal, identify affected objects/users, rotate secrets/URLs, follow breach-notice commitments, and complete root-cause review.
- Failed update: stop execution, preserve telemetry, invoke rollback before the agreed decision deadline, restore coordinated application/database state, verify manual controls, and keep the incident open through one stable production cycle.
- Emergency stop: customer operator or authorized Green Pipe engineer cancels the job; the agent performs no further mutating operation and reports the last completed idempotency checkpoint.
