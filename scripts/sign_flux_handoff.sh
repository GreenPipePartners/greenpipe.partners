#!/usr/bin/env bash
set -euo pipefail

handoff_dir="${1:-.runtime/greenpipe-handoff}"
version="${2:-0.1.0}"
release_dir="${handoff_dir}/release/flux/${version}"
release_root="${handoff_dir}/release/flux"
docs_dir="${handoff_dir}/docs/flux/${version}"
bundle_path=".runtime/greenpipe-signed-handoff-flux-${version}.tar.gz"

required_files=(
  "${release_dir}/flux-${version}.tar.zst"
  "${release_dir}/flux-${version}.tar.zst.sha256"
  "${release_dir}/flux-deploy.py"
  "${release_dir}/flux-deploy.py.sha256"
  "${release_dir}/flux-docs-${version}.tar.zst"
  "${release_dir}/flux-docs-${version}.tar.zst.sha256"
  "${release_dir}/manifest.example.json"
  "${release_dir}/manifest.example.yaml"
  "${docs_dir}/index.html"
)

for required_file in "${required_files[@]}"; do
  if [ ! -f "${required_file}" ]; then
    printf 'Missing required file: %s\n' "${required_file}" >&2
    exit 1
  fi
done

for checksum_file in "${release_dir}"/*.sha256; do
  checksum_name="$(basename "${checksum_file}")"
  (cd "${release_dir}" && sha256sum -c "${checksum_name}")
done

: "${FLUX_RELEASE_GPG_KEY_ID:?FLUX_RELEASE_GPG_KEY_ID is required}"
: "${FLUX_RELEASE_GPG_PASSPHRASE:?FLUX_RELEASE_GPG_PASSPHRASE is required}"

gpg --batch --armor --export "${FLUX_RELEASE_GPG_KEY_ID}" > "${release_root}/flux-release.pub"

for checksum_file in "${release_dir}"/*.sha256; do
  signed_file="${checksum_file%.sha256}"
  gpg \
    --batch \
    --yes \
    --pinentry-mode loopback \
    --passphrase "${FLUX_RELEASE_GPG_PASSPHRASE}" \
    --local-user "${FLUX_RELEASE_GPG_KEY_ID}" \
    --armor \
    --detach-sign \
    --output "${signed_file}.sig" \
    "${signed_file}"
done

for signature_file in "${release_dir}"/*.sig; do
  gpg --batch --verify "${signature_file}" "${signature_file%.sig}"
done

python - "${release_dir}" "${version}" <<'PY'
import json
import sys
from pathlib import Path

release_dir = Path(sys.argv[1])
version = sys.argv[2]
base_url = f"https://greenpipe.partners/release/flux/{version}"
public_key_url = "https://greenpipe.partners/release/flux/flux-release.pub"
checksum_file = release_dir / f"flux-{version}.tar.zst.sha256"
sha256 = checksum_file.read_text(encoding="utf-8").split()[0]

manifest = {
    "apiVersion": "flux.greenpipe.partners/v1",
    "kind": "FluxInstall",
    "metadata": {"deployment_id": "dep_123"},
    "spec": {
        "release": {
            "version": version,
            "artifact_url": f"{base_url}/flux-{version}.tar.zst",
            "sha256": sha256,
            "checksum_url": f"{base_url}/flux-{version}.tar.zst.sha256",
            "signature_url": f"{base_url}/flux-{version}.tar.zst.sig",
            "public_key_url": public_key_url,
        },
        "target": {"allowed_hosts": "localhost,127.0.0.1", "web_bind": "0.0.0.0:8000"},
        "database": {"mode": "local"},
        "services": {"enable": True, "start": True},
    },
}

(release_dir / "manifest.example.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=False) + "\n",
    encoding="utf-8",
)
(release_dir / "manifest.example.yaml").write_text(
    f"""apiVersion: flux.greenpipe.partners/v1
kind: FluxInstall
metadata:
  deployment_id: dep_123
spec:
  release:
    version: {version}
    artifact_url: {base_url}/flux-{version}.tar.zst
    sha256: {sha256}
    checksum_url: {base_url}/flux-{version}.tar.zst.sha256
    signature_url: {base_url}/flux-{version}.tar.zst.sig
    public_key_url: {public_key_url}
  target:
    allowed_hosts: localhost,127.0.0.1
    web_bind: 0.0.0.0:8000
  database:
    mode: local
  services:
    enable: true
    start: true
""",
    encoding="utf-8",
)
PY

mkdir -p "$(dirname "${bundle_path}")"
tar -C "${handoff_dir}" -czf "${bundle_path}" README.md release docs

printf 'Signed handoff bundle: %s\n' "${bundle_path}"
