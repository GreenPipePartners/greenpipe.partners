from django.test import SimpleTestCase

from .gists import _render_report_markdown


class LogicReportEmbedTests(SimpleTestCase):
    def test_same_site_logic_report_gets_tall_frame(self):
        for page in ('index.html', 'logic.html', 'resources.html', 'screens.html'):
            with self.subTest(page=page):
                html = _render_report_markdown(f'<iframe src="https://greenpipe.partners/static/portal/logic-reports/washheat-rev-o/{page}" title="WashHeat viewer"></iframe>')
                self.assertIn('class="report-embed report-logic-embed"', html)
                self.assertIn('title="WashHeat viewer"', html)
                self.assertIn('allowfullscreen', html)

    def test_regular_embeds_retain_standard_frame(self):
        for url in ('https://example.com/static/portal/logic-reports/demo/index.html', 'https://greenpipe.partners/other/index.html', 'https://link.excalidraw.com/readonly/example'):
            with self.subTest(url=url):
                html = _render_report_markdown(f'<iframe src="{url}"></iframe>')
                self.assertNotIn('report-logic-embed', html)
                self.assertIn('class="report-embed"', html)

    def test_non_https_and_inline_scripts_still_escaped(self):
        html = _render_report_markdown('<iframe src="javascript:alert(1)"></iframe>\n\n<script>alert(1)</script>')
        self.assertNotIn('<iframe ', html)
        self.assertNotIn('<script>', html)

    def test_logic_embed_in_code_fence_is_not_activated(self):
        html = _render_report_markdown('```html\n<iframe src="https://greenpipe.partners/static/portal/logic-reports/demo/index.html"></iframe>\n```')
        self.assertNotIn('<iframe ', html)
        self.assertIn('class="language-html"', html)
        self.assertNotIn('class="report-embed', html)
