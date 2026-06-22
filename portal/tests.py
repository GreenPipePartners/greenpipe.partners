import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import override_settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .gists import parse_gist_id
from .models import Report


GIST_ID = "6a946f178f4b6df48b30ef12e500ccd0"


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
        self.assertContains(response, "The open-source manufacturing development platform")
        self.assertContains(response, "Start running the controls workbench in Linux")
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
        self.assertContains(response, "https://github.com/Bobby-Miller/Fluxy")
        self.assertContains(response, "Flux")
        self.assertContains(response, "Fluxy")

    def test_docs_landing_redirects_to_starlight_latest(self):
        response = self.client.get(reverse("portal:docs"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/docs/flux/latest/")

    def test_install_page_is_removed(self):
        response = self.client.get("/install")

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
    def test_admin_managed_report_renders_gist_report_and_source_files(self, mock_urlopen):
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
        self.assertContains(response, "sample_file.sql")
        self.assertContains(response, "language-sql")
        self.assertContains(response, "select 1")
        self.assertContains(response, "sample_python_file.py")
        self.assertContains(response, "language-python")
        self.assertContains(response, "print(&#x27;hello world!&#x27;)")
        self.assertNotContains(response, GIST_ID)
        self.assertNotContains(response, "Source")
        self.assertNotContains(response, "Open Gist")

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
