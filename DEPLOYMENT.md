# Deployment

This project is shaped for an agent-managed Django deployment on Render.

## Local checks

```bash
uv sync
uv run python manage.py check
uv run python manage.py test
uv run python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the homepage, `http://127.0.0.1:8000/about/` for About, `http://127.0.0.1:8000/docs/flux/latest/` for Flux docs, and `http://127.0.0.1:8000/health/` for the health check.

Astro/Starlight docs can be previewed with `npm run docs:dev` and built with `npm run docs:build`. Docs builds require Node `>=22.12.0`.

## Render setup

1. Create a Render Blueprint from this GitHub repository.
2. Render reads `render.yaml` and creates the Docker-backed `greenpipe-partners` web service and `greenpipe-partners-db` Postgres database on the `basic-256mb` instance type.
3. Point DNS for `greenpipe.partners` and `www.greenpipe.partners` to Render after the service is live.
4. Keep secret values and billing in Render; keep code, settings, and service shape in Git.

## Database

The app uses SQLite only as a local fallback. Render should use managed Postgres by default via `DATABASE_URL` from `greenpipe-partners-db`.

The Docker start command runs `python manage.py migrate --noinput` before Gunicorn so deployed environments stay current.

## Production notes

- Static files are collected during the Docker build and served by Whitenoise.
- Astro/Starlight docs are built during the Docker build and served by Django from `.runtime/site` until signed docs are published under `GREENPIPE_PUBLISH_ROOT`.
- Render health checks use `/health/`.
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, CSRF origins, and `DATABASE_URL` are environment-driven.
- The frontend is Django templates plus HTMX, not a React/SPA stack.
- Flux and fluxy long-form docs are authored with Astro/Starlight. Decide before production whether docs publish from this service, a Render static site, or `docs.greenpipe.partners`.
- Astro production output is `.runtime/site/` and should be mounted as static docs, not rendered by Django per request.
- The Flux deployment contract lives in `greenpipe-website-contract.md`; the website publishes typed install intent, release artifacts, checksums, signatures, manifests, and status views only.
- Fluxup is the primary installer UX: `uvx fluxup init`.
- Reports are hidden direct URLs managed through Django admin. They fetch GitHub Gists by ID and require `report.md`.
- Django admin is mounted at `/control/`.

## Admin bootstrap

The Docker start command runs `python manage.py ensure_admin` after migrations.

Set these Render environment variables to create/update an admin user:

- `DJANGO_SUPERUSER_USERNAME`: defaults to `admin` in `render.yaml`
- `DJANGO_SUPERUSER_EMAIL`: defaults to `admin@greenpipe.partners` in `render.yaml`
- `DJANGO_SUPERUSER_PASSWORD`: secret value, must be set in Render

Set `GITHUB_TOKEN` in Render if report Gist API calls need higher rate limits or private Gist access.

## Release signing

Use `.github/workflows/flux-release-sign.yml` to sign Flux handoffs before publishing.

Set up a protected GitHub environment named `flux-release-signing` with required reviewers and these secrets:

- `FLUX_RELEASE_GPG_PRIVATE_KEY`
- `FLUX_RELEASE_GPG_KEY_ID`
- `FLUX_RELEASE_GPG_PASSPHRASE`

Add `FLUX_ARTIFACT_READ_TOKEN` if the workflow must read artifacts from a private Flux repo run.

Current workflow defaults:

- `source_repository`: `GreenPipePartners/Flux`
- `source_run_id`: `27916772023`
- `handoff_artifact_name`: `greenpipe-handoff`
- `flux_version`: `0.1.0`
- `publish_to_repo`: `true`

With `publish_to_repo=true`, the workflow commits the signed handoff to `published/greenpipe-handoff`, which is the default `GREENPIPE_PUBLISH_ROOT` used by Django and Render.

The signer exports `published/greenpipe-handoff/release/flux/flux-release.pub`; Fluxup verifies release signatures from `https://greenpipe.partners/release/flux/flux-release.pub`.

If branch protection blocks direct workflow commits, run with `publish_to_repo=false`, download the signed handoff artifact, unpack it into `published/greenpipe-handoff`, and commit it through the normal review path.
- Keep `render.yaml` and this runbook updated whenever deployment shape changes.
