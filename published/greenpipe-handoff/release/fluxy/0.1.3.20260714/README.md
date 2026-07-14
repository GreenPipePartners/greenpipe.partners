# Fluxy Free Public Beta 0.1.3.20260714

Fluxy Free is a third-party Ignition Gateway module for the Fluxy Python client. It is not certified, approved, supported, or endorsed by Inductive Automation.

## Downloads

- `Fluxy-Ignition81-Free-0.1.3.20260714.modl`: Ignition 8.1.50+
- `Fluxy-Ignition83-Free-0.1.3.20260714.modl`: Ignition 8.3.4+

Install only the artifact matching the Gateway's major version. Both artifacts use module ID `com.greenpipepartners.fluxy`, set `freeModule=true`, and require no Fluxy module entitlement.

## Signing

This public beta is self-signed by `CN=Green Pipe Partners, LLC`.

- Certificate SHA-256 fingerprint: `F8:FE:15:C6:BE:62:CC:24:78:C4:25:0F:90:4F:74:72:37:83:07:D5:62:30:77:65:78:27:5A:5B:83:DD:15:64`
- Certificate SHA-1 thumbprint displayed by Ignition: `07:48:38:5C:E2:37:80:FB:58:B1:51:CF:34:54:80:D3:59:47:17:F4`
- Validity: July 14, 2026 through July 13, 2029
- Public certificate: `Fluxy-Beta-Signing-Certificate.pem`

Review the certificate identity and fingerprint during Ignition's module installation flow. Do not enable unsigned modules.

## Integrity

```text
16170c3ece7fc9ba99990734bd7d22c69ba34974dc1118ac6ffd7fa6ff7f3971  Fluxy-Ignition81-Free-0.1.3.20260714.modl
d5d41ecf84a075e562e9d29daf06fcc26c24df478b9c4026689d70c98eb56ea6  Fluxy-Ignition83-Free-0.1.3.20260714.modl
cec996660c03316d300c3da4b169a3f61a2388ec27953aeadd9cafea1a240f4d  Fluxy-Beta-Signing-Certificate.pem
```

SHA-256 sidecars and target-specific CycloneDX SBOMs are attached.

## Source

- Tag: `v0.1.3.20260714`
- Commit: `b89f8048b4f5d46cabae059a64035e964f34d152`
- Source: https://github.com/GreenPipePartners/Fluxy-modl/tree/v0.1.3.20260714
- License: MPL-2.0

The pre-vendor descriptor intentionally omits the optional IA `vendorId` field. The globally unique module ID remains `com.greenpipepartners.fluxy`.

## Verification

- Compiled and tested against Ignition SDK 8.1.50, 8.1.51, 8.3.4, and 8.3.6.
- GitHub source and tagged-release workflows passed.
- Both signed archives passed source identity, metadata, SBOM, required-class, bundled-host-class, and checksum audits.
- The 8.3 artifact was installed with unsigned-module mode disabled.
- Authenticated project scan, tag configuration/read/write/delete, audit query, historian browse/query/store/stream, and cleanup tests passed on Ignition 8.3.4.

## Known Limits

- This is a self-signed public beta, not an IA Module Showcase release.
- The 8.1 artifact was compile- and unit-tested but not installed on a live 8.1 Gateway during this release.
- Historian operations require a licensed or active-trial Ignition historian module and a configured provider.
