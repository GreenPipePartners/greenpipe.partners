# Hanwha WashHeat report displays

Registered as an Engineering Report for Hanwha through portal migration 0009. Migration 0010 removes the report revision label from its displayed title.

- Report: <https://greenpipe.partners/reports/Hanwha/e0b8e388d5adbe939b6f2ab8895d9426>
- Authoring Gist: <https://gist.github.com/Bobby-Miller/e0b8e388d5adbe939b6f2ab8895d9426>
- Delivery packages: <https://github.com/GreenPipePartners/greenpipe.partners/releases/tag/hanwha-washheat-rev-o-2026-09-18>
- Static viewers: `/static/portal/logic-reports/washheat-rev-o/`

`report.md` is the current authoring scaffold: three standalone iframe blocks and no narrative. The Gist contains only this file so the customer can supply their own written content. `Press-Manual-Update.md` is an archived source document from the initial publication; it is no longer attached to the Gist or rendered in the report. `publication.json` records the current Gist snapshot and static asset hashes. `SHA256SUMS.txt` identifies the original release archives.

The report uses the existing Gist renderer. Standalone HTTPS iframe blocks embed PLC logic, Ignition screens and supplemental calculations/diagrams, with Calculation flow selected initially. A narrowly scoped renderer class gives these viewers a taller frame; the existing report model, customer list and theme control provide the surrounding page. Same-origin viewers observe the site's theme, including their prebuilt images. The report title, captions and viewer interface omit publication revision labels.

Toolbars retain zoom, fit width, full screen, PLC rung selection and Open SVG for diagrams. Drawings use SVG with automatic PNG fallback. The image-format selector, Copy link, source links, Open image and View JSON are omitted. PLC legends retain the color/group keys; the PLC and Perspective explanatory paragraphs are omitted.

## Contents

- 39 PLC routine/AOI drawings, 903 source rungs, searchable FDC / Presses / CDLs hierarchy.
- Database schema, message translation and calculation-flow resource table.
- Three Perspective views represented by six captured screen states, with source correspondence retained in the manifest.
- Prebuilt dark and light SVG/PNG assets; no PLC parsing or Excalidraw runtime on the reader's device.
- Source listings, verification evidence and separate editable FDC / Presses / CDLs Excalidraw downloads.
- Portable Obsidian report, Studio-check package and standalone web-viewer ZIP as release assets.

## Engineering status

Both press changes require manual updates to the current live programs. Packaged press ACD/L5X files are offline references, not deployment baselines. FDC arrival observations have ±1-second advisory uncertainty and supplement the operator's stopwatch. Live implementation and commissioning are pending.

Perspective captures contain synthetic lab records. Their light images are report-only color adaptations of the original native screenshots.

## Verification and deployment

The source delivery records 50 viewer browser checks, 16 embedded-view checks and 252 theme-matched diagram-strip comparisons. The website's report tests additionally exercise the three-display scaffold, customer-list registration, revision-neutral title, static links and all three embed classes.

Run `python manage.py check`, `python manage.py test`, and production-mode `python manage.py collectstatic --noinput`. Render auto-deploys the repository's main branch and runs migrations before starting Gunicorn. After deployment, verify the report URL, all three frames, host-theme propagation, source links and release downloads.
