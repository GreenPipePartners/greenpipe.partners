# Fluxy Free Public Beta 0.2.0.20260714

Fluxy Free is a third-party Ignition Gateway module for the Fluxy Python client. It is not certified, approved, supported, or endorsed by Inductive Automation.

## Downloads

- `Fluxy-Ignition81-Free-0.2.0.20260714.modl`: Ignition 8.1.50+
- `Fluxy-Ignition83-Free-0.2.0.20260714.modl`: Ignition 8.3.4+

Install only the artifact matching the Gateway's major version. Both artifacts use module ID `partners.greenpipe.fluxy`, set `freeModule=true`, and require no Fluxy module entitlement.

## Changes

- Expanded the native module contract from 13 routes to 28 declared operations on Ignition 8.3 and 26 available operations on Ignition 8.1.
- Added authenticated tag copy, move, rename, import, export, and query routes.
- Added historian aggregate, annotation, and Ignition 8.3 metadata routes.
- Added installed-module and project inventory routes.
- Added `util/getCapabilities` with explicit version availability and Read/Write classifications.
- Added one shared, fail-closed route manifest consumed by both module targets and checked against each Jython dispatcher.
- Added 1 MiB request, 4 MiB response, collection, query-page, and aggregate-result limits.
- Extended mutation auditing without recording imported tag definitions, values, annotation data, metadata values, credentials, or complete request bodies.

## Signing

This public beta is self-signed by `CN=Green Pipe Partners, LLC`.

- Certificate SHA-256 fingerprint: `F8:FE:15:C6:BE:62:CC:24:78:C4:25:0F:90:4F:74:72:37:83:07:D5:62:30:77:65:78:27:5A:5B:83:DD:15:64`
- Certificate SHA-1 thumbprint displayed by Ignition: `07:48:38:5C:E2:37:80:FB:58:B1:51:CF:34:54:80:D3:59:47:17:F4`
- Validity: July 14, 2026 through July 13, 2029
- Public certificate: `Fluxy-Beta-Signing-Certificate.pem`

Review the certificate identity and fingerprint during Ignition's module installation flow. Do not enable unsigned modules.

## Integrity

```text
dfe38fb5bad3616907932e8429cd20de0fa2a96ce5c2bac263ada7fdaf0b6c48  Fluxy-Ignition81-Free-0.2.0.20260714.modl
e5264e828eef27260a6bfe4f234667e9c09a73ccf91001ff795963d3e3f05e64  Fluxy-Ignition83-Free-0.2.0.20260714.modl
cec996660c03316d300c3da4b169a3f61a2388ec27953aeadd9cafea1a240f4d  Fluxy-Beta-Signing-Certificate.pem
```

SHA-256 sidecars and target-specific CycloneDX SBOMs are included.

## Source

- Tag: `v0.2.0.20260714`
- Commit: `be856fcd7a8410de6338a7d7d5cc9953899aeff8`
- Source: https://github.com/GreenPipePartners/Fluxy-modl/tree/v0.2.0.20260714
- License: MPL-2.0

IA identifies Green Pipe as the author through the assigned `partners.greenpipe` module prefix. No separate numeric vendor ID is required in `module.xml`.

## Verification

- Compiled and tested against Ignition SDK 8.1.50, 8.1.51, 8.3.4, and 8.3.6.
- Both dispatchers compile under the corresponding Ignition Jython 2.7 runtime.
- Both signed archives passed source identity, metadata, SBOM, exact route-manifest, required-class, bundled-host-class, and checksum audits.
- The signed 8.3 artifact was installed with unsigned-module mode disabled.
- Ignition reported `partners.greenpipe.fluxy` version `0.2.0.20260714`, state `ACTIVE`, license state `Free`, and contract version 2.
- Authenticated capability discovery, module inventory, project scan, and tag copy/move/rename/import/export/query lifecycle tests passed on Ignition 8.3.4.

## Known Limits

- This is a self-signed public beta, not an IA Module Showcase release.
- The 8.1 artifact was compile- and unit-tested but not installed on a live 8.1 Gateway during this release.
- Advanced historian routes were compile- and contract-tested, but their live 8.3 lifecycle could not complete because the test Gateway's Historian module demo period had expired and rejected data storage.
- Historian and audit operations require the applicable licensed or active-trial Ignition modules and configured providers.
