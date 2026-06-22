# Green Pipe Django hosting direction

## Context

The repository currently has a static `index.html` plus an early Django skeleton (`green_pipe_config`, `portal`). Traffic is expected to be low, but the site should be long-lived and inexpensive.

## Recommendation

Use a small Django application deployed on a low-maintenance PaaS, with Postgres as the default database target for any deployed environment.

Preferred path: **Render web service + Render managed Postgres**. SQLite can remain a local development fallback, but the application should be shaped and verified against Postgres before production deployment.

Why this path:

- Lower operational burden than a VPS.
- Cheaper and simpler than AWS/GCP/Azure for this scale.
- Durable enough for a business site if the app is containerized and settings are environment-driven.
- Easy migration path from static marketing page to authenticated/reporting portal.

## Advisable options

### 1. Render / Railway / Fly.io PaaS

Best fit for: low-traffic Django site with occasional dynamic features.

Use:

- Gunicorn serving Django.
- Whitenoise for static files.
- Environment variables for `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `DATABASE_URL`.
- Managed Postgres as the default deploy database, not a later retrofit.
- Custom domains for `greenpipe.partners` and `www.greenpipe.partners`.

Tradeoff: modest monthly cost and some platform lock-in, but low maintenance.

### 2. Small VPS

Best fit for: maximum longevity and cost control.

Use:

- Hetzner/DigitalOcean/Linode small instance.
- Docker Compose with Django, Caddy or Nginx, and Postgres.
- Automated backups and OS patching.

Tradeoff: cheapest durable compute, but you own security patches, backups, TLS, monitoring, and recovery.

### 3. PythonAnywhere

Best fit for: simplest Django hosting with minimal DevOps.

Tradeoff: easy, stable, and Django-friendly; less flexible for custom deployment patterns and subdomain routing.

### 4. Keep static front page + separate dynamic app

Best fit for: preserving GitHub Pages reliability while adding a small portal.

Use:

- `greenpipe.partners` remains GitHub Pages or another static host.
- `greenpipe.partners` runs Django.

Tradeoff: very reliable marketing page, but two deployment targets and duplicated styling unless shared carefully.

## Initial build slice

1. Convert `index.html` into Django templates: `base.html`, `home.html`, shared static assets.
2. Add production settings driven by environment variables.
3. Add Gunicorn and Whitenoise.
4. Add a health check route.
5. Add deployment manifest for the chosen host.
6. Add Render managed Postgres and wire `DATABASE_URL` in the deployment manifest/environment.
7. Run migrations against Postgres during deploy, even if the first visible feature is mostly static.
8. Add subdomain/path routing for report pages after the base deployment is stable.

## Risks

- Current runtime defaults still fall back to local SQLite; treat this as development-only and verify deploy behavior with Postgres.
- `pyproject.toml` currently requires Python `>=3.14`, which may limit host compatibility; target a widely supported production Python version when deploying.
- Private/report URLs should not rely only on obscure gist keys; add access control if the reports contain client-sensitive material.
