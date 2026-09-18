from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from .models import Report


GIST_ID = "e0b8e388d5adbe939b6f2ab8895d9426"
SNAPSHOT = Path(settings.BASE_DIR) / "docs/reports/hanwha-washheat-rev-o"
STATIC_PREFIX = "/static/portal/logic-reports/washheat-rev-o/"


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.frames = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if tag == "iframe":
            self.frames.append(attrs)


class WashHeatReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.report = Report.objects.get(customer="Hanwha", gist_id=GIST_ID)

    def render_report(self):
        gist = {
            "description": "Hanwha WashHeat Automation",
            "files": {
                name: {"content": (SNAPSHOT / name).read_text(), "type": "text/markdown"}
                for name in ("report.md",)
            },
        }
        with patch("portal.gists._fetch_json", return_value=gist):
            response = self.client.get(self.report.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        return response

    def test_registered_as_hanwha_engineering_report_in_existing_list(self):
        self.assertEqual(self.report.report_type, Report.ReportType.ENGINEERING)
        self.assertEqual(self.report.title, "WashHeat Automation")
        response = self.client.get(reverse("portal:customer_reports", kwargs={
            "customer": "Hanwha", "access_key": GIST_ID,
        }))
        self.assertContains(response, self.report.get_absolute_url())
        self.assertIn(self.report.get_absolute_url(), [r["url"] for r in response.context["engineering_reports"]])
        self.assertTrue(response.context["weekly_reports"])

    def test_report_contains_only_the_three_displays(self):
        response = self.render_report()
        links = Links(response.content.decode())
        self.assertEqual(len(links.frames), 3)
        self.assertEqual({urlparse(f["src"]).path for f in links.frames}, {
            STATIC_PREFIX + page for page in ("logic.html", "resources.html", "screens.html")
        })
        self.assertContains(response, 'class="report-embed report-logic-embed"', count=3)
        self.assertEqual([frame["title"] for frame in links.frames], [
            "PLC logic", "Ignition screens", "Supplemental calculations and diagrams",
        ])
        self.assertNotContains(response, 'data-report-document')
        self.assertNotContains(response, "Revision O")
        self.assertNotContains(response, "Downloadable delivery")
        self.assertTrue(all(line.startswith("<iframe ") for line in (SNAPSHOT / "report.md").read_text().splitlines() if line))

    def test_display_links_resolve_and_calculations_are_initially_selected(self):
        links = Links(self.render_report().content.decode())
        static_links = [urlparse(href) for href in links.links]
        static_links = [url for url in static_links if url.path.startswith(STATIC_PREFIX)]
        self.assertEqual(len(static_links), 3)
        for url in static_links:
            with self.subTest(path=url.path, fragment=url.fragment):
                self.assertIsNotNone(finders.find(unquote(url.path.removeprefix("/static/"))))
        self.assertEqual(static_links[-1].fragment, "logic-washheat-resources-rev-o/calculation-flow")
