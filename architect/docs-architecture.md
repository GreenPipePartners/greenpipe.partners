# Documentation architecture direction

## Decision

Use Astro/Starlight for Flux and fluxy product documentation.

The Django site remains the Flux marketing and portal application. Astro/Starlight owns long-form product documentation and should be linked from the Django design as first-class product docs.

## Products

- Flux is the flagship Green Pipe controls workbench and should receive the primary documentation emphasis.
- Fluxup is the installer CLI for Flux and is the public install CTA.
- fluxy is the free open-source Python library for connecting Ignition to Python 3.

## Implementation guidance

- Author docs under `src/content/docs/` and configure navigation in `astro.config.mjs`.
- Keep marketing copy concise in Django templates; move detailed how-to material into Starlight pages.
- Build product docs in the Flux repo, hand them off as `greenpipe-handoff`, and sign that handoff in the website repo.
- Commit signed handoff output to `published/greenpipe-handoff` for Render to serve.
- Serve Flux docs at `/docs/flux/0.1.0/` and redirect `/docs/flux/latest/` to the current version.
- Serve the Flux release public key at `/release/flux/flux-release.pub`.
- Sign release handoffs in GitHub Actions using the protected `flux-release-signing` environment before publishing artifacts or docs.
- Keep the Django site server-rendered with HTMX; do not introduce a React/SPA docs shell.

## Build slice

1. Add Starlight source pages for Flux and fluxy.
2. Add `npm run docs:dev` and `npm run docs:build` to local docs instructions.
3. Run `.github/workflows/flux-release-sign.yml` against the Flux handoff artifact.
4. Publish signed artifacts and docs from `published/greenpipe-handoff`.

## Risks

- If docs are served from the same Django app, URL ownership around `/docs/` must be explicit.
- If docs are hosted separately, cross-links from Django must be environment-driven before production.
- The website must publish install intent and artifacts only. It must not SSH into targets or generate arbitrary root shell strings.
