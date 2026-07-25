import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from .gists import _snippet_anchor_id
from .models import Release, Report


GIST_ID = "9a946f178f4b6df48b30ef12e500ccd3"


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.payload


class ReportCodeSectionUnitTests(SimpleTestCase):
    def test_snippet_anchor_ids_are_stable_and_collision_resistant(self):
        anchor = _snippet_anchor_id("query one.sql")

        self.assertEqual(anchor, _snippet_anchor_id("query one.sql"))
        self.assertNotEqual(anchor, _snippet_anchor_id("query-one.sql"))
        self.assertTrue(anchor.startswith("report-code-query-one-sql-"))
        self.assertTrue(_snippet_anchor_id("!!!").startswith("report-code-file-"))

    def test_frontend_expands_hash_targeted_disclosures(self):
        script = (Path(__file__).resolve().parent / "static" / "portal" / "site.js").read_text()
        styles = (Path(__file__).resolve().parent / "static" / "portal" / "styles.css").read_text()

        self.assertIn("decodeURIComponent(hash.slice(1))", script)
        self.assertIn("document.getElementById(targetId)", script)
        self.assertIn('section.matches("[data-report-code-section]")', script)
        self.assertIn("disclosure.open = true", script)
        self.assertIn('window.addEventListener("hashchange"', script)
        self.assertIn("section.scrollIntoView", script)
        self.assertIn('button.setAttribute("aria-label", "Copy code")', script)
        self.assertIn('linkButton.setAttribute("aria-label", "Copy link to this section")', script)
        self.assertIn('directLink.hash = section.id', script)
        self.assertNotIn("document.querySelector(window.location.hash)", script)
        self.assertIn("--report-code-bg: #1d2021", styles)
        self.assertIn(".report-shell .hljs-comment", styles)
        self.assertIn(".report-shell .hljs-keyword", styles)
        self.assertIn(".report-code-section:target", styles)
        self.assertIn(".report-code-disclosure[open]", styles)
        self.assertIn(".report-code-disclosure:not([open]) > :not(summary)", styles)


class ReportCodeSectionIntegrationTests(TestCase):
    @patch("portal.gists.urlopen")
    def test_report_renders_appendable_collapsed_code_accordions(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            json.dumps(
                {
                    "files": {
                        "report.md": {"content": "# Review", "truncated": False},
                        "query one.sql": {"content": "select 1;", "truncated": False},
                        "query-one.sql": {"content": "select 2;", "truncated": False},
                    }
                }
            ).encode("utf-8")
        )
        Report.objects.create(
            customer="TEST",
            report_type=Report.ReportType.ENGINEERING,
            title="Code review",
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        response = self.client.get(f"/reports/TEST/{GIST_ID}")
        first_anchor = _snippet_anchor_id("query one.sql")
        second_anchor = _snippet_anchor_id("query-one.sql")
        response_html = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com;",
            response["Content-Security-Policy"],
        )
        self.assertContains(response, "Code and queries")
        self.assertContains(response, "highlight.js/11.11.1/highlight.min.js")
        self.assertContains(response, "data-report-code-section", count=2)
        self.assertContains(response, 'class="report-code-disclosure" data-report-code-block', count=2)
        self.assertContains(response, f'id="{first_anchor}"')
        self.assertContains(response, f'id="{second_anchor}"')
        self.assertLess(response_html.index(f'id="{first_anchor}"'), response_html.index(f'id="{second_anchor}"'))
        self.assertNotIn("data-report-code-block open", response_html)
        self.assertNotContains(response, "report-code-index")
        self.assertNotContains(response, "report-code-permalink")

    @patch("portal.gists.urlopen")
    def test_release_source_files_keep_expanded_layout(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            json.dumps(
                {
                    "files": {
                        "release.md": {"content": "# Release", "truncated": False},
                        "upgrade.py": {"content": "print('upgrade')", "truncated": False},
                    }
                }
            ).encode("utf-8")
        )
        Release.objects.create(
            topic="test release",
            release_date=date(2026, 7, 25),
            gist_url=f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        )

        response = self.client.get("/release/test%20release/2026-07-25")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "upgrade.py")
        self.assertContains(response, "highlight.js/11.11.1/highlight.min.js")
        self.assertContains(response, "language-python")
        self.assertNotContains(response, "Code and queries")
        self.assertNotContains(response, "data-report-code-section")
        self.assertNotContains(response, "data-report-code-block")
