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

Primary install UX is `sudo "$(command -v uvx)" fluxup init`. The public CTA also provides a Python venv fallback for machines without `uv`.

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

The Gist must contain `report.md` or `Report.md`. HTTPS iframe tags in the report are rendered as sandboxed, responsive embeds. Other files in the Gist are rendered as source snippets based on file extension, for example `.sql` as SQL and `.py` as Python.

## Daily Schedules

Schedules use the report publishing flow: one secret GitHub Gist containing
`report.md` per day, and one `Report` record with type **Daily schedule**. Use a
shared `customer` value as the trip slug, `customer_name` as the trip name, and
set both dates to that day's date. The title is the short daily focus.

```text
/schedule/{trip}/{gist_id}
/schedule/{trip}/all/{any_registered_schedule_gist_id}
```

Each day has chronological day tabs and previous/next links. **All days** shows
the complete itinerary; **Print all days / PDF** starts each day on a new sheet.
Keep each Markdown source concise enough to fit one Letter page. The root
`/schedule/` is a neutral landing page; trip links are direct-only. Schedule
responses request no indexing and no referrer, and omit public trip listings.

The existing Gist Markdown renderer supplies the content. Schedule Gists are
cached server-side for 60 seconds, so edits appear within about a minute. Flight
and session times should remain exact; round only flexible planning blocks and
label commute allowances as estimates. No calendar or booking is changed.

Validate with `uv run python manage.py check`, `uv run python manage.py
makemigrations --check --dry-run`, and `uv run python manage.py test portal`.
Check a mobile viewport and print the all-days view to confirm one sheet per day.
Publish through the existing Render deployment after the schema/data migrations
and Gists are ready. The September 21–25 ICC trip is registered by migration
`0012_add_icc_2026_schedule`; its content lives in the five Gists.

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

## PanelLock

PanelLock is mounted at `/panellock/`; invitation-only customer access starts at `/panellock/portal/`. The selector stores server-priced proposal requests with a 30% PC markup and 15% panel-display markup, and preserves each supplied OnLogic configuration URL. External hardware and Ignition list prices are cached in `CatalogOffer` and reviewed monthly with `python manage.py review_panellock_catalog`.

Operational, retention, legal-topic, and threat-model recommendations live in `PANELLOCK_OPERATIONS.md`. Reusable AgentLabs authenticate with Ed25519 signatures and replay nonces, reach the portal through an independent uplink, and use a separate non-bridged Ethernet work link to harden a selected panel PC. The panel PC does not run the portal agent; MAC addresses are inventory only.
