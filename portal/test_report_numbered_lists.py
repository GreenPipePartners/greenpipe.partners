import json
from io import BytesIO
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from .gists import _render_report_markdown
from .models import Report


HANWHA_GIST_ID = "2b6da293f23d0d8fa4c12829338b785e"
HANWHA_REPORT_MARKDOWN = (
    "## Combustion Air Pressure Budget Calculation\n"
    "The combination of the combustion air demand and the highest-resistance path "
    "was used as a pressure resistance basis, and we evaluated the static pressure "
    "budget in 2 scenarios:\n\n"
    "1) The manual air flow valve fully open\n"
    "2) The manual air flow valve restricted to 50%-travel\n\n"
    "# Analysis and observation\n"
    "From the final chart, we expect to be able to reach ~590 ACFM (35,400 ACFH) "
    "on a fully open combustion air system as currently designed. At 50%-travel, "
    "we should be able to reach ~540 ACFM (32,400 ACFH). "
    "Two major factors can contribute to this:\n\n"
    "1) Air fan performance\n"
    "2) Additional pressure resistance\n\n"
    "## Air fan performance\n"
    "Last week, we took apart the fan and evaluated it for degradation, poor "
    "installation, or other defects."
)


class ReportNumberedListTests(SimpleTestCase):
    def test_renders_dot_and_parenthesis_markers_as_ordered_lists(self):
        for marker in (".", ")"):
            with self.subTest(marker=marker):
                report_html = _render_report_markdown(
                    "Two major factors can contribute to this:\n\n"
                    f"1{marker} Air fan performance\n"
                    f"2{marker} Additional pressure resistance"
                )

                self.assertHTMLEqual(
                    report_html,
                    "<p>Two major factors can contribute to this:</p>"
                    "<ol><li>Air fan performance</li>"
                    "<li>Additional pressure resistance</li></ol>",
                )

    def test_preserves_the_starting_number(self):
        for marker in (".", ")"):
            with self.subTest(marker=marker):
                report_html = _render_report_markdown(
                    f"3{marker} Air fan performance\n"
                    f"3{marker} Additional pressure resistance"
                )

                self.assertHTMLEqual(
                    report_html,
                    '<ol start="3"><li>Air fan performance</li>'
                    "<li>Additional pressure resistance</li></ol>",
                )

    def test_renders_parenthesized_lists_nested_in_both_list_types(self):
        for marker, next_marker, tag in (("-", "-", "ul"), ("1.", "2.", "ol"), ("1)", "2)", "ol")):
            with self.subTest(marker=marker):
                report_html = _render_report_markdown(
                    f"{marker} Factors\n"
                    "    1) Air fan performance\n"
                    "        - Check rotation\n"
                    "    2) Additional pressure resistance\n"
                    f"{next_marker} Recommendation"
                )

                self.assertHTMLEqual(
                    report_html,
                    f"<{tag}><li>Factors<ol><li>Air fan performance"
                    "<ul><li>Check rotation</li></ul></li>"
                    "<li>Additional pressure resistance</li></ol></li>"
                    f"<li>Recommendation</li></{tag}>",
                )

    def test_renders_multiline_and_loose_list_items(self):
        report_html = _render_report_markdown(
            "1) Air fan\n"
            "   performance\n\n"
            "    Inspect the blower.\n\n"
            "2) Additional pressure resistance"
        )

        self.assertHTMLEqual(
            report_html,
            "<ol><li><p>Air fan performance</p><p>Inspect the blower.</p></li>"
            "<li><p>Additional pressure resistance</p></li></ol>",
        )

    def test_keeps_numbered_examples_in_code_blocks_literal(self):
        content = "1) Air fan performance\n2) Additional pressure resistance"
        for code in (
            f"```text\n{content}\n```",
            f"~~~text\n{content}\n~~~",
            "\n".join(f"    {line}" for line in content.splitlines()),
        ):
            with self.subTest(code=code):
                report_html = _render_report_markdown(code)

                self.assertIn("<pre><code", report_html)
                self.assertIn(content, report_html)
                self.assertNotIn("<ol", report_html)

    def test_keeps_inline_numbers_and_escaped_markers_literal(self):
        for content, expected_html in (
            ("`1) Air fan performance`", "<p><code>1) Air fan performance</code></p>"),
            (r"1\) Air fan performance", "<p>1) Air fan performance</p>"),
            (
                "Factors: 1) Air fan performance 2) Additional pressure resistance",
                "<p>Factors: 1) Air fan performance 2) Additional pressure resistance</p>",
            ),
        ):
            with self.subTest(content=content):
                self.assertHTMLEqual(_render_report_markdown(content), expected_html)

    def test_numbered_callouts_keep_task_lists_and_attachment_links(self):
        report_html = _render_report_markdown(
            "> [!recommendation]\n"
            "> 1) [ ] Check the [fan](./fan.py)\n"
            "> 2) [x] Inspect the air line",
            {"fan.py": "report-code-fan"},
        )

        self.assertIn('class="report-callout report-callout-recommendation"', report_html)
        self.assertIn('<ol class="report-task-list">', report_html)
        self.assertEqual(report_html.count('type="checkbox"'), 2)
        self.assertEqual(report_html.count('disabled="disabled"'), 2)
        self.assertEqual(report_html.count('checked="checked"'), 1)
        self.assertIn('href="#report-code-fan"', report_html)

    def test_numbered_lists_keep_raw_html_escaped(self):
        report_html = _render_report_markdown("1) <script>alert(1)</script>\n2) **Safe**")

        self.assertIn("<ol>", report_html)
        self.assertNotIn("<script>", report_html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", report_html)
        self.assertIn("<li><strong>Safe</strong></li>", report_html)


class HanwhaReportNumberedListTests(TestCase):
    @patch("portal.gists.urlopen")
    def test_report_renders_both_numbered_lists_without_rewriting_markdown(self, mock_urlopen):
        mock_urlopen.return_value = BytesIO(
            json.dumps(
                {"files": {"report.md": {"content": HANWHA_REPORT_MARKDOWN, "truncated": False}}}
            ).encode("utf-8")
        )
        Report.objects.create(
            customer="Hanwha",
            report_type=Report.ReportType.ENGINEERING,
            title="Report on Air Flow Expectation on the Age 1 Bell Furnace",
            gist_url=f"https://gist.github.com/Bobby-Miller/{HANWHA_GIST_ID}",
        )

        response = self.client.get(f"/reports/Hanwha/{HANWHA_GIST_ID}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<ol>", count=2)
        self.assertContains(
            response,
            "<ol><li>The manual air flow valve fully open</li>"
            "<li>The manual air flow valve restricted to 50%-travel</li></ol>",
            html=True,
        )
        self.assertContains(
            response,
            "<ol><li>Air fan performance</li><li>Additional pressure resistance</li></ol>",
            html=True,
        )
        self.assertContains(response, "~590 ACFM (35,400 ACFH)")
        self.assertContains(response, "~540 ACFM (32,400 ACFH)")
        self.assertEqual(response.context["gist_report"]["report_markdown"], HANWHA_REPORT_MARKDOWN)
