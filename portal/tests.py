import hashlib
import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .gists import _render_report_markdown, parse_gist_id
from .models import Release, Report


GIST_ID = "6a946f178f4b6df48b30ef12e500ccd0"
OTHER_GIST_ID = "7b946f178f4b6df48b30ef12e500ccd1"
THIRD_GIST_ID = "8c946f178f4b6df48b30ef12e500ccd2"


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.payload


class PortalSmokeTests(SimpleTestCase):
    def test_homepage_renders(self):
        response = self.client.get(reverse("portal:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Green Pipe Partners")
        self.assertContains(response, "/logo_hollow.png")
        self.assertContains(response, "/static/portal/favicon.ico")
        self.assertContains(response, "Introducing Flux: A Green Pipe Solution")
        self.assertContains(response, "The open-source manufacturing development platform")
        self.assertContains(response, "Start running the controls workbench in Linux")
        self.assertContains(response, "WARNING: Flux is")
        self.assertContains(response, "VERY MUCH")
        self.assertContains(response, "Please explore, but do be careful")
        self.assertContains(response, 'data-component="tabs"')
        self.assertContains(response, "data-copy")
        self.assertContains(response, 'data-component="copy-status"')
        self.assertContains(response, "Run by UV")
        self.assertContains(response, "Run by Python")
        self.assertContains(response, "uvx ")
        self.assertContains(response, "fluxup init")
        self.assertContains(response, "python3 -m venv /tmp/fluxup")
        self.assertContains(response, "/tmp/fluxup/bin/fluxup init")
        self.assertContains(response, "https://github.com/GreenPipePartners/Flux")
        self.assertContains(response, "controls workbench")
        self.assertContains(response, "/docs/flux/latest/")
        self.assertContains(response, "/about/")
        self.assertNotContains(response, "Fluxup GitHub")
        self.assertNotContains(response, "Flux GitHub")
        self.assertNotContains(response, "Install details")
        self.assertNotContains(response, "/install")
        self.assertNotContains(response, "curl -fsSLO https://greenpipe.partners/release/flux/0.1.0/flux-deploy.py")
        self.assertNotContains(response, "PyPI Trusted Publishing")
        self.assertNotContains(response, "/api/flux/deployments/dep_123/manifest")
        self.assertNotContains(response, "--claim-token")
        self.assertContains(response, "Flux")
        self.assertContains(response, "/about/")
        self.assertNotContains(response, "Services")
        self.assertNotContains(response, "We get Flux running in your world")
        self.assertNotContains(response, "ESXi-compatible environments")
        self.assertNotContains(response, "Time-series data consolidation")
        self.assertNotContains(response, "LLM subscription management")
        self.assertNotContains(response, "Remote Hub")
        self.assertNotContains(response, "Reports")

    def test_about_page_renders(self):
        response = self.client.get(reverse("portal:about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Green Pipe Partners is a software company")
        self.assertContains(response, "open-source industrial and manufacturing development tools")
        self.assertContains(response, "https://github.com/GreenPipePartners/Flux")
        self.assertContains(response, "https://github.com/GreenPipePartners/Fluxy")
        self.assertContains(response, "Flux")
        self.assertContains(response, "Fluxy")

    def test_fluxy_page_renders_signed_downloads(self):
        response = self.client.get(reverse("portal:fluxy"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fluxy Free public beta")
        self.assertContains(response, "0.1.6.20260714")
        self.assertContains(response, "Ignition 8.3")
        self.assertContains(response, "Ignition 8.1")
        self.assertContains(response, "Green Pipe Partners, LLC")
        self.assertContains(response, "F8:FE:15:C6:BE:62:CC:24")
        self.assertContains(response, "/release/fluxy/0.1.6.20260714/Fluxy-Ignition83-Free-0.1.6.20260714.modl")
        self.assertContains(response, "/release/fluxy/0.1.6.20260714/Fluxy-Ignition81-Free-0.1.6.20260714.modl")
        self.assertContains(response, "https://github.com/GreenPipePartners/Fluxy-modl")
        self.assertContains(response, "partners.greenpipe.fluxy")
        self.assertContains(response, "Install fluxy-ign")
        self.assertContains(response, "https://pypi.org/project/fluxy-ign/")
        self.assertContains(response, "python -m pip install fluxy-ign")
        self.assertContains(response, "[default]fluxy")
        self.assertContains(response, "X-Ignition-API-Token")
        self.assertContains(response, "Hello World")
        self.assertContains(response, "/docs/flux/0.1.0/fluxy/", count=6)
        self.assertContains(response, "/docs/flux/0.1.0/fluxy/#authentication")
        self.assertContains(response, "/docs/flux/0.1.0/fluxy/#install-the-gateway-module", count=2)
        self.assertContains(response, "not certified, approved, supported, or endorsed")
        self.assertNotContains(response, "backed by public MPL-2.0 source")
        self.assertNotContains(response, ".unsigned.modl")

    def test_fluxy_artifacts_are_served_and_match_published_checksums(self):
        version = "0.1.6.20260714"
        release_root = (
            Path(__file__).resolve().parents[1]
            / "published"
            / "greenpipe-handoff"
            / "release"
            / "fluxy"
            / version
        )

        for ignition_line in ("81", "83"):
            filename = f"Fluxy-Ignition{ignition_line}-Free-{version}.modl"
            artifact = release_root / filename
            expected = (release_root / f"{filename}.sha256").read_text().split()[0]
            self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), expected)

            response = self.client.get(f"/release/fluxy/{version}/{filename}")
            self.assertEqual(response.status_code, 200)
            response_digest = hashlib.sha256(b"".join(response.streaming_content)).hexdigest()
            self.assertEqual(response_digest, expected)

    def test_fluxy_latest_metadata_points_to_tagged_release(self):
        response = self.client.get("/release/fluxy/latest.json")

        self.assertEqual(response.status_code, 200)
        payload = json.loads(b"".join(response.streaming_content))
        self.assertEqual(payload["version"], "0.1.6.20260714")
        self.assertEqual(payload["channel"], "public-beta")
        self.assertEqual(
            payload["source"],
            "https://github.com/GreenPipePartners/Fluxy-modl/tree/v0.1.6.20260714",
        )

    def test_agentlab_page_renders(self):
        response = self.client.get(reverse("portal:agentlab"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AgentLab Training for Controls Engineers")
        self.assertContains(response, "Three-Day Agent Workbench Deep Dive")
        self.assertContains(response, "practical Linux-based agent workbench")
        self.assertContains(response, "applies AI workflows to real controls engineering work")
        self.assertContains(response, "Set up the engineering workstations")
        self.assertContains(response, "Build each attendee's Ubuntu VM lab")
        self.assertContains(response, "Apply the lab to your site")
        self.assertContains(response, "Day 4 (Optional)")
        self.assertContains(response, "Build a Rockwell Windows VM with AI agents")
        self.assertContains(response, "Onsite Training")
        self.assertContains(response, "$6,900")
        self.assertContains(response, "Base Training Price")
        self.assertContains(response, "Linux AgentLab with Omarchy")
        self.assertContains(response, "Linux AgentLab with Ubuntu")
        self.assertContains(response, "Bring Your Own Setup")
        self.assertContains(response, "Build out Rockwell Controls VM")
        self.assertContains(response, "$2,200 one time")
        self.assertContains(response, "Includes 1 controls VM license")
        self.assertContains(response, "Additional Controls VM Licenses")
        self.assertContains(response, 'max="4"')
        self.assertContains(response, "$250 each")
        self.assertContains(response, "A ChatGPT Pro plan is required and is not provided")
        self.assertContains(response, "https://chatgpt.com/?ifpazk=1k0d2&amp;default_tab=personal&amp;highlight_plan=pro#pricing")
        self.assertContains(response, "Valid for 30 days")
        self.assertContains(response, "Travel and onsite expenses may add cost")
        self.assertContains(response, "Generate Proposal")
        self.assertNotContains(response, "PDF quotes are generated locally")
        self.assertNotContains(response, "Flux and Fluxy")
        self.assertNotContains(response, "Omarchy lab image")
        self.assertNotContains(response, "3.2K OLED touch display")
        self.assertNotContains(response, "Mandatory package")
        self.assertNotContains(response, "AILab Training")
        self.assertContains(response, "data-ailab-quote")

    def test_old_ailab_url_is_removed(self):
        response = self.client.get("/ailab/")

        self.assertEqual(response.status_code, 404)

    def test_docs_landing_redirects_to_starlight_latest(self):
        response = self.client.get(reverse("portal:docs"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/docs/flux/latest/")

    def test_install_page_is_removed(self):
        response = self.client.get("/install")

        self.assertEqual(response.status_code, 404)

    def test_admin_is_mounted_at_control(self):
        response = self.client.get("/control/")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/control/login/"))

    def test_admin_default_path_is_not_mounted(self):
        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 404)

    def test_release_typo_redirects_to_canonical_path(self):
        response = self.client.get("/realease/flux/0.1.0/flux-0.1.0.tar.zst")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/release/flux/0.1.0/flux-0.1.0.tar.zst")

    def test_release_file_serves_from_publish_root(self):
        with TemporaryDirectory() as temp_dir:
            publish_root = Path(temp_dir)
            release_dir = publish_root / "release" / "flux" / "0.1.0"
            release_dir.mkdir(parents=True)
            (release_dir / "flux-deploy.py").write_text("print('flux')\n")

            with override_settings(GREENPIPE_PUBLISH_ROOT=publish_root):
                response = self.client.get("/release/flux/0.1.0/flux-deploy.py")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(b"".join(response.streaming_content), b"print('flux')\n")

    def test_release_public_key_serves_from_publish_root(self):
        with TemporaryDirectory() as temp_dir:
            publish_root = Path(temp_dir)
            release_dir = publish_root / "release" / "flux"
            release_dir.mkdir(parents=True)
            (release_dir / "flux-release.pub").write_text("public key\n")

            with override_settings(GREENPIPE_PUBLISH_ROOT=publish_root):
                response = self.client.get("/release/flux/flux-release.pub")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(b"".join(response.streaming_content), b"public key\n")

    def test_flux_docs_latest_redirects_to_version(self):
        response = self.client.get(reverse("portal:flux_docs_latest"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/docs/flux/0.1.0/")

    def test_fluxy_docs_source_contains_current_installation_guide(self):
        docs_source = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "content"
            / "docs"
            / "fluxy"
            / "index.mdx"
        ).read_text()

        self.assertIn("python -m pip install fluxy-ign", docs_source)
        self.assertIn("Fluxy Free", docs_source)
        self.assertIn("X-Ignition-API-Token", docs_source)
        self.assertIn("[default]fluxy", docs_source)
        self.assertIn("Hello World", docs_source)
        self.assertIn("partners.greenpipe", docs_source)
        self.assertIn("/docs/flux/0.1.0/fluxy/gateway-functions/", docs_source)

    def test_fluxy_gateway_function_reference_lists_every_module_route(self):
        reference = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "content"
            / "docs"
            / "fluxy"
            / "gateway-functions.mdx"
        ).read_text()
        routes = {
            "util/getVersion",
            "util/queryAuditLog",
            "tag/readBlocking",
            "tag/browse",
            "tag/getConfiguration",
            "tag/configure",
            "tag/writeBlocking",
            "tag/deleteTags",
            "historian/browse",
            "historian/queryRawPoints",
            "historian/queryRawPointsStream",
            "historian/storeDataPoints",
            "project/requestScan",
        }

        self.assertIn("13 authenticated Gateway functions", reference)
        for route in routes:
            self.assertIn(route, reference)

    def test_flux_docs_serve_from_publish_root(self):
        with TemporaryDirectory() as temp_dir:
            publish_root = Path(temp_dir)
            docs_dir = publish_root / "docs" / "flux" / "0.1.0"
            docs_dir.mkdir(parents=True)
            (docs_dir / "index.html").write_text("<h1>Flux docs</h1>")

            with override_settings(GREENPIPE_PUBLISH_ROOT=publish_root):
                response = self.client.get("/docs/flux/0.1.0/")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(b"".join(response.streaming_content), b"<h1>Flux docs</h1>")

    def test_flux_docs_fall_back_to_local_docs_build(self):
        with TemporaryDirectory() as temp_dir:
            publish_root = Path(temp_dir) / "missing-publish-root"
            local_docs = Path(temp_dir) / ".runtime" / "site"
            local_docs.mkdir(parents=True)
            (local_docs / "index.html").write_text("<h1>Local Flux docs</h1>")

            with override_settings(GREENPIPE_PUBLISH_ROOT=publish_root, BASE_DIR=Path(temp_dir)):
                response = self.client.get("/docs/flux/0.1.0/")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(b"".join(response.streaming_content), b"<h1>Local Flux docs</h1>")

    def test_health_check_returns_ok(self):
        response = self.client.get(reverse("portal:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_logo_asset_is_served(self):
        response = self.client.get(reverse("portal:logo"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")



class ReportMarkdownTests(SimpleTestCase):
    def test_renders_obsidian_callouts_and_youtube_links(self):
        report_html = _render_report_markdown(
            "> [!success] Recommendation\n"
            "> Advance the **pilot**.\n\n"
            "[Flux demonstration](https://youtu.be/DG2SbUPBALs)\n\n"
            "> [!quote] The decision in one sentence\n"
            "> Move forward with confidence.\n\n"
            "[Supporting material](https://example.com/demo)"
        )

        self.assertIn('class="report-callout report-callout-recommendation"', report_html)
        self.assertIn('<div class="report-callout-title">Recommendation</div>', report_html)
        self.assertIn("Advance the <strong>pilot</strong>.", report_html)
        self.assertIn('class="report-callout report-callout-quote"', report_html)
        self.assertIn('<div class="report-callout-title">The decision in one sentence</div>', report_html)
        self.assertIn('src="https://www.youtube-nocookie.com/embed/DG2SbUPBALs"', report_html)
        self.assertIn('title="Flux demonstration"', report_html)
        self.assertIn('loading="lazy"', report_html)
        self.assertIn('<a href="https://example.com/demo">Supporting material</a>', report_html)
        self.assertEqual(report_html.count('class="report-video"'), 1)


class ReportTests(TestCase):
    def test_parse_gist_id_from_full_url(self):
        gist_id = parse_gist_id(f"https://gist.github.com/Bobby-Miller/{GIST_ID}")

        self.assertEqual(gist_id, GIST_ID)

    def test_report_model_derives_gist_id_and_url(self):
        report = Report.objects.create(
            customer="PRW",
            customer_name="Johnny Ortega",
            start_date="2026-06-01",
            end_date="2026-06-05",
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        self.assertEqual(report.gist_id, GIST_ID)
        self.assertEqual(report.get_absolute_url(), f"/reports/PRW/{GIST_ID}")
        self.assertEqual(str(report), "PRW / 2026-06-01 - 2026-06-05")

    @patch("portal.gists.urlopen")
    def test_report_customer_can_contain_spaces(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            json.dumps(
                {"files": {"report.md": {"content": "# Prairie Works Report", "truncated": False}}}
            ).encode("utf-8")
        )
        report = Report.objects.create(
            customer="Prairie Works",
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        self.assertEqual(report.get_absolute_url(), f"/reports/Prairie%20Works/{GIST_ID}")

        response = self.client.get(report.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Prairie Works Report")
        self.assertContains(response, f'href="/reports/Prairie%20Works/all/{GIST_ID}"')
        self.assertEqual(self.client.get(f"/reports/Prairie%20Works/all/{GIST_ID}").status_code, 200)

    def test_engineering_report_model_does_not_require_dates(self):
        report = Report.objects.create(
            customer="MOG",
            customer_name="Magnolia Oil & Gas",
            report_type=Report.ReportType.ENGINEERING,
            title="Chemical Data Integration Review",
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        self.assertIsNone(report.start_date)
        self.assertIsNone(report.end_date)
        self.assertEqual(report.gist_id, GIST_ID)
        self.assertEqual(report.get_absolute_url(), f"/reports/MOG/{GIST_ID}")
        self.assertEqual(str(report), "MOG / Chemical Data Integration Review")

    def test_report_admin_shows_destination_url_after_create(self):
        user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        report = Report.objects.create(
            customer="PRW",
            customer_name="Johnny Ortega",
            start_date="2026-06-01",
            end_date="2026-06-05",
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        self.client.force_login(user)
        response = self.client.get(f"/control/portal/report/{report.pk}/change/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Destination URL")
        self.assertContains(response, f'href="{report.get_absolute_url()}"')

    def test_report_admin_hides_destination_url_before_create(self):
        user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )

        self.client.force_login(user)
        response = self.client.get("/control/portal/report/add/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Destination URL")

    @patch("portal.gists.urlopen")
    def test_admin_managed_report_renders_gist_report_and_source_files(self, mock_urlopen):
        csv_content = "asset,hours\n" + "\n".join(f"Pump {index},{index}" for index in range(1, 31))
        mock_urlopen.return_value = FakeResponse(
            json.dumps(
                {
                    "description": "Sample report",
                    "files": {
                        "report.md": {
                            "filename": "report.md",
                            "content": "# Daily Report\n\nAll systems normal.\n\n<img alt=\"trend\" src=\"https://gist.github.com/user-attachments/assets/3a9cbdea-c464-4cea-bc7f-077bd96267fe\" />\n\n| Job | Hours |\n| --- | ---: |\n| 11008 | 8 |",
                            "truncated": False,
                        },
                        "diagram.png": {
                            "filename": "diagram.png",
                            "type": "image/png",
                            "raw_url": "https://gist.githubusercontent.com/Bobby-Miller/gist/raw/diagram.png",
                            "truncated": False,
                        },
                        "metrics.csv": {
                            "filename": "metrics.csv",
                            "content": csv_content,
                            "type": "text/csv",
                            "raw_url": "https://gist.githubusercontent.com/Bobby-Miller/gist/raw/metrics.csv",
                            "truncated": False,
                        },
                        "sample_file.sql": {
                            "filename": "sample_file.sql",
                            "content": "select 1\n",
                            "language": "SQL",
                            "truncated": False,
                        },
                        "sample_python_file.py": {
                            "filename": "sample_python_file.py",
                            "content": "print('hello world!')\n",
                            "language": "Python",
                            "truncated": False,
                        },
                    },
                }
            ).encode("utf-8")
        )
        Report.objects.create(
            customer="PRW",
            customer_name="Johnny Ortega",
            start_date="2026-06-01",
            end_date="2026-06-05",
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        response = self.client.get(f"/reports/PRW/{GIST_ID}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PRW")
        self.assertContains(response, "Weekly Report for June 1st, 2026 to June 5th, 2026.")
        self.assertContains(response, "Prepared for Johnny Ortega")
        self.assertContains(response, "Print report")
        self.assertContains(response, "Copy as Markdown")
        self.assertContains(response, "All PRW reports")
        self.assertContains(response, f'href="/reports/PRW/all/{GIST_ID}"')
        self.assertContains(response, "Daily Report")
        self.assertContains(response, "All systems normal.")
        self.assertContains(response, "<table>")
        self.assertContains(response, "<th>Job</th>")
        self.assertContains(response, "<td>11008</td>")
        self.assertContains(
            response,
            'src="https://gist.github.com/user-attachments/assets/3a9cbdea-c464-4cea-bc7f-077bd96267fe"',
        )
        self.assertContains(response, 'alt="trend"')
        self.assertContains(response, "diagram.png")
        self.assertContains(response, 'src="https://gist.githubusercontent.com/Bobby-Miller/gist/raw/diagram.png"')
        self.assertContains(response, "CSV Attachments")
        self.assertContains(response, "metrics.csv")
        self.assertContains(response, "<th>asset</th>")
        self.assertContains(response, "<td>Pump 24</td>")
        self.assertContains(response, "Previewing the first 25 rows.")
        self.assertContains(response, f'href="/reports/PRW/{GIST_ID}/csv/metrics.csv"')
        self.assertContains(response, "Download CSV")
        self.assertNotContains(response, "Pump 25")
        self.assertNotContains(response, "language-csv")
        self.assertContains(response, "sample_file.sql")
        self.assertContains(response, "language-sql")
        self.assertContains(response, "select 1")
        self.assertContains(response, "sample_python_file.py")
        self.assertContains(response, "language-python")
        self.assertContains(response, "print(&#x27;hello world!&#x27;)")
        self.assertNotContains(response, "Source")
        self.assertNotContains(response, "Open Gist")

    @patch("portal.gists.urlopen")
    def test_report_csv_download_uses_attachment_response(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            json.dumps(
                {
                    "files": {
                        "report.md": {"content": "# Daily Report", "truncated": False},
                        "metrics.csv": {
                            "filename": "metrics.csv",
                            "content": "asset,hours\nPump 1,1\n",
                            "type": "text/csv",
                            "truncated": False,
                        },
                    }
                }
            ).encode("utf-8")
        )
        Report.objects.create(
            customer="PRW",
            customer_name="Johnny Ortega",
            start_date="2026-06-01",
            end_date="2026-06-05",
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        response = self.client.get(f"/reports/PRW/{GIST_ID}/csv/metrics.csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertTrue(response["Content-Disposition"].startswith("attachment;"))
        self.assertIn("metrics.csv", response["Content-Disposition"])
        self.assertEqual(response.content, b"asset,hours\nPump 1,1\n")

    def test_customer_report_list_is_hidden_by_report_gist_id_and_grouped_by_type(self):
        Report.objects.create(
            customer="PRW",
            customer_name="Johnny Ortega",
            start_date="2026-05-26",
            end_date="2026-05-30",
            gist_url=f"https://gist.github.com/Bobby-Miller/{OTHER_GIST_ID}",
        )
        Report.objects.create(
            customer="PRW",
            customer_name="Johnny Ortega",
            start_date="2026-06-01",
            end_date="2026-06-05",
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )
        Report.objects.create(
            customer="PRW",
            customer_name="Johnny Ortega",
            report_type=Report.ReportType.ENGINEERING,
            title="Valve Review",
            gist_url=f"https://gist.github.com/Bobby-Miller/{THIRD_GIST_ID}",
        )

        response = self.client.get(f"/reports/PRW/all/{GIST_ID}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PRW Reports")
        self.assertContains(response, "Weekly Reports")
        self.assertContains(response, "Engineering Reports")
        self.assertContains(response, "Weekly Report")
        self.assertContains(response, "June 1, 2026 to June 5, 2026")
        self.assertContains(response, "May 26, 2026 to May 30, 2026")
        self.assertContains(response, "Valve Review")
        self.assertContains(response, f'href="/reports/PRW/{GIST_ID}"')
        self.assertContains(response, f'href="/reports/PRW/{THIRD_GIST_ID}"')

        content = response.content.decode("utf-8")
        self.assertLess(content.index("Weekly Reports"), content.index("Engineering Reports"))
        self.assertEqual(self.client.get(f"/reports/MOG/all/{GIST_ID}").status_code, 404)

    def test_customer_report_list_hides_empty_report_type_groups(self):
        Report.objects.create(
            customer="PRW",
            customer_name="Johnny Ortega",
            start_date="2026-06-01",
            end_date="2026-06-05",
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        response = self.client.get(f"/reports/PRW/all/{GIST_ID}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Weekly Reports")
        self.assertNotContains(response, "Engineering Reports")
        self.assertNotContains(response, "No engineering reports available")

    @patch("portal.gists.urlopen")
    def test_engineering_report_renders_generic_heading_and_uppercase_report_file(self, mock_urlopen):
        report_markdown = """# Magnolia Oil & Gas -- Chemical Data Integration Engineering Report

## Source Systems Included

| Source Provider | Source Code | Current Trial Scope |
| --- | ---: | --- |
| ChampionX | `CHX` | Historical backload |

## Review Request

```sql
SELECT source_code
FROM MDS.CHEM.chemical_lab_result_wide_by_day_location;
```
"""
        mock_urlopen.return_value = FakeResponse(
            json.dumps(
                {
                    "description": "Magnolia Chemical Analysis Datastore Review",
                    "files": {
                        "Report.md": {
                            "filename": "Report.md",
                            "content": report_markdown,
                            "truncated": False,
                        },
                        "analysis.sql": {
                            "filename": "analysis.sql",
                            "content": "select source_code from mds.chem.chemical_lab_result_wide_by_day_location;\n",
                            "language": "SQL",
                            "truncated": False,
                        },
                    },
                }
            ).encode("utf-8")
        )
        Report.objects.create(
            customer="MOG",
            customer_name="Magnolia Oil & Gas",
            report_type=Report.ReportType.ENGINEERING,
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        response = self.client.get(f"/reports/MOG/{GIST_ID}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MOG Engineering Report")
        self.assertContains(response, "Magnolia Chemical Analysis Datastore Review")
        self.assertContains(response, "Prepared for Magnolia Oil &amp; Gas")
        self.assertContains(response, "Magnolia Oil &amp; Gas -- Chemical Data Integration Engineering Report")
        self.assertContains(response, "Source Systems Included")
        self.assertContains(response, "language-sql")
        self.assertContains(response, "MDS.CHEM.chemical_lab_result_wide_by_day_location")
        self.assertContains(response, "analysis.sql")
        self.assertNotContains(response, "Weekly Report for")
        self.assertNotContains(response, "Report.md")

    @patch("portal.gists.urlopen")
    def test_report_requires_report_md(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            json.dumps({"files": {"sample_file.sql": {"content": "select 1", "truncated": False}}}).encode(
                "utf-8"
            )
        )
        Report.objects.create(
            customer="PRW",
            customer_name="Johnny Ortega",
            start_date="2026-06-01",
            end_date="2026-06-05",
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        response = self.client.get(f"/reports/PRW/{GIST_ID}")

        self.assertEqual(response.status_code, 404)

    def test_report_url_is_hidden_without_admin_record(self):
        response = self.client.get(f"/reports/PRW/{GIST_ID}")

        self.assertEqual(response.status_code, 404)

    def test_reports_index_is_not_public(self):
        response = self.client.get("/reports/")

        self.assertEqual(response.status_code, 404)


class ReleaseTests(TestCase):
    def test_release_model_normalizes_topic_and_derives_public_url(self):
        release = Release(
            topic="Flux Updates",
            release_date=date(2026, 7, 14),
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )
        release.full_clean()
        release.save()

        self.assertEqual(release.topic, "flux updates")
        self.assertEqual(release.gist_id, GIST_ID)
        self.assertEqual(release.get_absolute_url(), "/release/flux%20updates/2026-07-14")
        self.assertEqual(str(release), "flux updates / 2026-07-14")

    def test_release_admin_shows_destination_url_after_create(self):
        user = get_user_model().objects.create_superuser(
            username="release-admin",
            email="release-admin@example.com",
            password="password",
        )
        release = Release.objects.create(
            topic="flux",
            release_date=date(2026, 7, 14),
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        self.client.force_login(user)
        response = self.client.get(f"/control/portal/release/{release.pk}/change/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Destination URL")
        self.assertContains(response, f'href="{release.get_absolute_url()}"')

    @patch("portal.gists.urlopen")
    def test_public_release_renders_gist_and_links_to_release_index(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            json.dumps(
                {
                    "description": "Flux 0.2 is available",
                    "files": {
                        "Release.md": {
                            "filename": "Release.md",
                            "content": "# Flux 0.2\n\nThis release adds public notices.",
                            "truncated": False,
                        },
                        "upgrade.py": {
                            "filename": "upgrade.py",
                            "content": "print('upgrade')\n",
                            "language": "Python",
                            "truncated": False,
                        },
                        "compatibility.csv": {
                            "filename": "compatibility.csv",
                            "content": "platform,status\nLinux,supported\n",
                            "type": "text/csv",
                            "truncated": False,
                        },
                    },
                }
            ).encode("utf-8")
        )
        Release.objects.create(
            topic="flux",
            release_date=date(2026, 7, 14),
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        response = self.client.get("/release/flux/2026-07-14")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Flux 0.2 is available")
        self.assertContains(response, "Published July 14, 2026")
        self.assertContains(response, "This release adds public notices.")
        self.assertContains(response, "upgrade.py")
        self.assertContains(response, "language-python")
        self.assertContains(response, "compatibility.csv")
        self.assertContains(response, 'href="/release/flux/2026-07-14/csv/compatibility.csv"')
        self.assertContains(response, 'href="/release/"')
        self.assertContains(response, "All releases")
        self.assertNotContains(response, "Release.md")

    @patch("portal.gists.urlopen")
    def test_release_csv_download_uses_attachment_response(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            json.dumps(
                {
                    "files": {
                        "compatibility.csv": {
                            "filename": "compatibility.csv",
                            "content": "platform,status\nLinux,supported\n",
                            "type": "text/csv",
                            "truncated": False,
                        }
                    }
                }
            ).encode("utf-8")
        )
        Release.objects.create(
            topic="flux",
            release_date=date(2026, 7, 14),
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        response = self.client.get("/release/flux/2026-07-14/csv/compatibility.csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("compatibility.csv", response["Content-Disposition"])
        self.assertEqual(response.content, b"platform,status\nLinux,supported\n")

    def test_release_index_groups_by_topic_then_newest_date(self):
        for topic, release_date, gist_id in [
            ("flux", date(2026, 6, 1), GIST_ID),
            ("agent lab", date(2026, 7, 1), OTHER_GIST_ID),
            ("flux", date(2026, 7, 14), THIRD_GIST_ID),
        ]:
            Release.objects.create(
                topic=topic,
                release_date=release_date,
                gist_url=f"https://gist.github.com/Bobby-Miller/{gist_id}",
            )

        response = self.client.get("/release/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/release/agent%20lab/2026-07-01"')
        self.assertContains(response, 'href="/release/flux/2026-07-14"')
        self.assertContains(response, 'href="/release/flux/2026-06-01"')

        content = response.content.decode("utf-8")
        self.assertLess(content.index("<h2>Agent Lab</h2>"), content.index("<h2>Flux</h2>"))
        self.assertLess(content.index("July 14, 2026"), content.index("June 1, 2026"))

    @patch("portal.gists.urlopen")
    def test_release_requires_release_md(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            json.dumps({"files": {"notes.txt": {"content": "No release file", "truncated": False}}}).encode(
                "utf-8"
            )
        )
        Release.objects.create(
            topic="flux",
            release_date=date(2026, 7, 14),
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        response = self.client.get("/release/flux/2026-07-14")

        self.assertEqual(response.status_code, 404)

    def test_release_detail_rejects_invalid_or_unpublished_dates(self):
        self.assertEqual(self.client.get("/release/flux/2026-02-30").status_code, 404)
        self.assertEqual(self.client.get("/release/flux/2026-07-14").status_code, 404)
