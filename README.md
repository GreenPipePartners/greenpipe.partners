# Green Pipe Partners Website

Django-backed website for `greenpipe.partners`, prepared for agent-managed deployment on Render.

The app is server-rendered Django with HTMX enhancement. It intentionally avoids React and SPA frameworks.

## Local Development

```bash
uv sync
uv run python manage.py check
uv run python manage.py test
uv run python manage.py runserver
```

Homepage: `http://127.0.0.1:8000/`

Health check: `http://127.0.0.1:8000/health/`

About page: `http://127.0.0.1:8000/about/`

Fluxy downloads: `http://127.0.0.1:8000/fluxy/`

Flux docs: `http://127.0.0.1:8000/docs/flux/latest/`

## Product Docs

Flux and fluxy docs are authored with Astro/Starlight:

```bash
npm install
npm run docs:dev
npm run docs:build
```

Docs builds require Node `>=22.12.0`.

Astro builds to `.runtime/site/` for static mounting under `/docs/flux/0.1.0/`.

Flux is the flagship product. Fluxup is the installer CLI. The main service is getting Flux running in customer environments: ESXi-compatible sandboxing behind a Flux gateway, time-series consolidation, and LLM subscription management for controls platform users. fluxy is the open-source Ignition-to-Python library.

## Flux Deployment Contract

The website publishes install intent and release metadata. It must not SSH into targets or generate arbitrary root shell strings.

- Public install CTA is on `/`
- Canonical artifact route: `/release/flux/{version}/...`
- Fluxy module artifact route: `/release/fluxy/{version}/...`
- Public signing key route: `/release/flux/flux-release.pub`
- Typo route `/realease/...` redirects to `/release/...`
- Managed install API shape is documented in `greenpipe-website-contract.md`

Primary install UX is `uvx fluxup init`. The public CTA also provides a Python venv fallback for machines without `uv`.

Manual fallback uses the static release manifest at `/release/flux/0.1.0/manifest.example.json`. Managed installs use `/api/flux/deployments/{id}/manifest` after the API exists.

Signed release handoffs are produced by `.github/workflows/flux-release-sign.yml`.

Current Flux handoff defaults:

- `source_repository`: `GreenPipePartners/Flux`
- `source_run_id`: `27916772023`
- `handoff_artifact_name`: `greenpipe-handoff`
- `flux_version`: `0.1.0`

Required protected GitHub environment: `flux-release-signing`.

Required environment secrets:

- `FLUX_RELEASE_GPG_PRIVATE_KEY`: ASCII-armored private release signing key
- `FLUX_RELEASE_GPG_KEY_ID`: signing key ID or fingerprint
- `FLUX_RELEASE_GPG_PASSPHRASE`: signing key passphrase

Optional secret:

- `FLUX_ARTIFACT_READ_TOKEN`: token for reading handoff artifacts from another private repo

The workflow downloads a `greenpipe-handoff` artifact from the Flux build, signs files that have `.sha256` checksums, verifies signatures, uploads a signed bundle, and can commit the signed handoff into `published/greenpipe-handoff`.

`GREENPIPE_PUBLISH_ROOT` defaults to `published/greenpipe-handoff`, which makes Render serve the committed signed bundle directly.

## Hidden Reports

Reports are managed through Django admin with a customer value and a GitHub Gist URL.
Use the default `Weekly` type for date-bounded customer updates, or `Engineering` for generic engineering review reports that do not need weekly dates.

Admin is mounted at `/control/`.

The public URL shape is hidden/direct only:

```text
/reports/{customer}/{gist_id}
```

The Gist must contain `report.md` or `Report.md`. Other files in the Gist are rendered as source snippets based on file extension, for example `.sql` as SQL and `.py` as Python.

## Public Releases

Release notices are managed through Django admin with a topic, release date, and GitHub Gist URL. The Gist must contain `release.md` (case-insensitive); images, CSV attachments, and source files are rendered with the notice.

```text
/release/
/release/{topic}/{YYYY-MM-DD}
```

The public index groups releases by topic and lists the newest release dates first. These notice routes coexist with static release artifacts under `/release/{topic}/{version}/...`.

## Deployment

Render service and Postgres configuration lives in `render.yaml`. Operational notes live in `DEPLOYMENT.md`.

Render deploys with Docker. The image builds Astro/Starlight docs, collects Django static files, runs migrations on startup, and serves Django with Gunicorn.
