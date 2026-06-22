# Frontend architecture direction

## Decision

Build the Green Pipe web application as a server-rendered Django app enhanced with HTMX.

Do not use React, Vue, Svelte, Next.js, or similar SPA/client-side application frameworks for core product flows.

## Rationale

- Django templates keep routing, authorization, forms, and rendering close to the backend.
- HTMX provides enough interactivity for reports, portals, filtering, partial refreshes, and inline actions without introducing a separate frontend build system.
- Server-rendered pages are simpler to deploy on Render and easier to keep secure for customer/report views.
- The expected app shape favors durable business workflows over highly interactive canvas-style UI.

## Implementation guidance

- Use Django templates as the primary UI layer.
- Use HTMX attributes for targeted swaps, form submissions, filtering, pagination, and report refreshes.
- Return partial templates for HTMX requests and full-page templates for normal browser navigation.
- Keep JavaScript small, local, and dependency-light; prefer progressive enhancement.
- Use plain CSS or a small CSS utility/component approach only if needed; avoid adding a frontend bundler unless there is a specific need.

## Build slice

1. Add HTMX as a static asset or CDN include in the base Django template.
2. Define template conventions: full-page templates under `portal/templates/portal/`, partials under `portal/templates/portal/partials/`.
3. For each dynamic feature, implement one normal Django view first, then add HTMX partial behavior where it improves UX.
4. Keep tests focused on HTTP responses, template rendering, form handling, and permissions rather than browser framework behavior.

## Risks

- HTMX does not remove the need for clear backend state and authorization checks; every partial endpoint must enforce the same permissions as full-page views.
- Complex realtime or highly stateful interfaces may need small custom JavaScript, but should still avoid becoming an SPA by default.
