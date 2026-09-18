# Hanwha WashHeat engineering report — Revision O

Report dated **18 September 2026**, registered as an Engineering Report for Hanwha through portal migration 0009.

- Report: <https://greenpipe.partners/reports/Hanwha/e0b8e388d5adbe939b6f2ab8895d9426>
- Authoring Gist: <https://gist.github.com/Bobby-Miller/e0b8e388d5adbe939b6f2ab8895d9426>
- Delivery packages: <https://github.com/GreenPipePartners/greenpipe.partners/releases/tag/hanwha-washheat-rev-o-2026-09-18>
- Static viewers: `/static/portal/logic-reports/washheat-rev-o/`

`report.md` and `Press-Manual-Update.md` are publication snapshots of the Gist's two files. `publication.json` records their hashes, source correspondence and the deployed static asset hashes. `SHA256SUMS.txt` identifies the three release archives.

The narrative uses the existing Gist renderer. Standalone HTTPS iframe blocks embed `logic.html`, `resources.html` and `screens.html`. A narrowly scoped renderer class gives these viewers a taller frame; the existing report model, customer list and theme control provide the surrounding page. Same-origin viewers observe the site's theme, including their prebuilt images.

## Contents

- 39 PLC routine/AOI drawings, 903 source rungs, searchable FDC / Presses / CDLs hierarchy.
- Database schema, message translation and calculation-flow resource table.
- Three Perspective views represented by six captured screen states, linked to the exact released view JSON.
- Prebuilt dark and light SVG/PNG assets; no PLC parsing or Excalidraw runtime on the reader's device.
- Source listings, verification evidence and separate editable FDC / Presses / CDLs Excalidraw downloads.
- Portable Obsidian report, Studio-check package and standalone web-viewer ZIP as release assets.

## Engineering status

Both press changes require manual updates to the current live programs. Packaged press ACD/L5X files are offline references, not deployment baselines. FDC arrival observations have ±1-second advisory uncertainty and supplement the operator's stopwatch. Live implementation and commissioning are pending.

Perspective captures contain synthetic lab records. Their light images are report-only color adaptations of the original native screenshots.

## Verification and deployment

The source delivery records 50 viewer browser checks, 16 embedded-view checks and 252 theme-matched diagram-strip comparisons. The website's report tests additionally exercise the real narrative, customer-list registration, attachment links, static source links and all three embed classes.

Run `python manage.py check`, `python manage.py test`, and production-mode `python manage.py collectstatic --noinput`. Render auto-deploys the repository's main branch and runs migrations before starting Gunicorn. After deployment, verify the report URL, all three frames, host-theme propagation, source links and release downloads.
