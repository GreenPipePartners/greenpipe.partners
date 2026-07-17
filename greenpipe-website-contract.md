# GreenPipe Website Contract

This contract lets `greenpipe.partners` publish Flux installs and Flux Astro/Starlight documentation without becoming a remote shell or Flux runtime host.

## Install UX

Primary install UX:

```bash
sudo "$(command -v uvx)" fluxup init
```

Python fallback UX:

```bash
python3 -m venv /tmp/fluxup && /tmp/fluxup/bin/python -m pip install --upgrade fluxup && sudo /tmp/fluxup/bin/fluxup init
```

Managed install UX:

```bash
sudo "$(command -v uvx)" fluxup init \
  --manifest-url https://greenpipe.partners/api/flux/deployments/{id}/manifest \
  --claim-token <one-time-token> \
  --json
```

Keep `flux-deploy.py` as a fallback/manual path only.

## Repos

- Flux release source: <https://github.com/GreenPipePartners/Flux>
- Flux installer CLI: <https://github.com/GreenPipePartners/Fluxup>
- PyPI package target: `fluxup`

## Required Static Routes

Serve these from `GREENPIPE_PUBLISH_ROOT`:

```text
/release/flux/0.1.0/flux-0.1.0.tar.zst
/release/flux/0.1.0/flux-0.1.0.tar.zst.sha256
/release/flux/0.1.0/flux-0.1.0.tar.zst.sig
/release/flux/0.1.0/flux-deploy.py
/release/flux/0.1.0/flux-deploy.py.sha256
/release/flux/0.1.0/flux-deploy.py.sig
/release/flux/0.1.0/flux-docs-0.1.0.tar.zst
/release/flux/0.1.0/flux-docs-0.1.0.tar.zst.sha256
/release/flux/0.1.0/flux-docs-0.1.0.tar.zst.sig
/release/flux/flux-release.pub
/docs/flux/0.1.0/
/docs/flux/latest/ -> /docs/flux/0.1.0/
```

Canonical path is `/release/...`. If `/realease/...` appears, redirect it to `/release/...`.

## Signing Workflow

The website signing process must export the public GPG key:

```bash
gpg --armor --export "$FLUX_RELEASE_GPG_KEY_ID" \
  > .runtime/greenpipe-handoff/release/flux/flux-release.pub
```

`fluxup` defaults to verifying signatures with:

```text
https://greenpipe.partners/release/flux/flux-release.pub
```

## Flux Handoff Workflow

Use Flux artifact source:

- `source_repository`: `GreenPipePartners/Flux`
- `handoff_artifact_name`: `greenpipe-handoff`
- `flux_version`: `0.1.0`

Current successful Flux handoff run:

- `source_run_id`: `27916772023`

For future releases, use the latest successful Build GreenPipe handoff run from `GreenPipePartners/Flux`.

The website signing workflow publishes signed output under:

```text
published/greenpipe-handoff/
```

Django serves that path by default via `GREENPIPE_PUBLISH_ROOT`.

## Managed Manifest Shape

The website manifest should include:

```json
{
  "apiVersion": "flux.greenpipe.partners/v1",
  "kind": "FluxInstall",
  "metadata": {"deployment_id": "dep_123"},
  "spec": {
    "release": {
      "version": "0.1.0",
      "artifact_url": "https://greenpipe.partners/release/flux/0.1.0/flux-0.1.0.tar.zst",
      "sha256": "<hex-digest>",
      "checksum_url": "https://greenpipe.partners/release/flux/0.1.0/flux-0.1.0.tar.zst.sha256",
      "signature_url": "https://greenpipe.partners/release/flux/0.1.0/flux-0.1.0.tar.zst.sig",
      "public_key_url": "https://greenpipe.partners/release/flux/flux-release.pub"
    },
    "target": {"allowed_hosts": "localhost,127.0.0.1", "web_bind": "0.0.0.0:8000"},
    "database": {"mode": "local"},
    "services": {"enable": true, "start": true}
  }
}
```

## Deployment API

Minimum website API for managed installs:

```text
POST /api/flux/deployments
GET  /api/flux/deployments/{id}/manifest
POST /api/flux/deployments/{id}/events
POST /api/flux/deployments/{id}/complete
```

Event payload:

```json
{
  "deployment_id": "dep_123",
  "stage": "systemd",
  "state": "running",
  "message": "Rendering Flux systemd units",
  "timestamp": "2026-06-21T12:00:00Z"
}
```

## Website Rules

- Website is the control plane, not the runtime host.
- Do not SSH into targets.
- Do not generate arbitrary root shell commands.
- Publish signed artifacts, docs, manifests, install UI, and status/event views.
- Keep `flux-deploy.py` as a fallback/manual path, but lead with `fluxup`.
- Secrets must be claim-scoped or resolved by the target runner; do not expose database URLs in public release metadata.
