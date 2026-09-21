from datetime import date
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils.safestring import mark_safe

from .gists import GistError, _render_report_markdown
from .models import Report


class ScheduleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.days = [
            Report.objects.create(
                customer="test-trip",
                customer_name="Test trip",
                report_type=Report.ReportType.SCHEDULE,
                title=f"Day {number}",
                start_date=date(2026, 9, number),
                end_date=date(2026, 9, number),
                gist_url=f"https://gist.github.com/example/{number:032x}",
            )
            for number in (23, 21, 22)
        ]
        self.regular = Report.objects.create(
            customer="test-trip",
            title="Customer work report",
            gist_url=f"https://gist.github.com/example/{99:032x}",
        )
        self.loader = patch("portal.schedules.load_report_gist", side_effect=self.document).start()
        self.addCleanup(patch.stopall)
        self.addCleanup(cache.clear)

    @staticmethod
    def document(gist_id):
        number = int(gist_id, 16)
        return {"document_html": mark_safe(_render_report_markdown(
            f"| Time | Plan |\n| --- | --- |\n| 7–8 AM | Run on day {number}. |\n"
        ))}

    def test_single_day_has_chronological_navigation_and_only_its_content(self):
        response = self.client.get(self.days[2].get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Run on day 22.")
        self.assertNotContains(response, "Run on day 21.")
        self.assertNotContains(response, "Customer work report")
        self.assertEqual([day.start_date.day for day in response.context["days"]], [21, 22, 23])
        self.assertEqual(response.context["previous_day"].start_date.day, 21)
        self.assertEqual(response.context["next_day"].start_date.day, 23)
        self.assertContains(response, 'aria-current="page"', count=1)
        self.loader.assert_called_once_with(self.days[2].gist_id)

    def test_all_days_uses_one_print_section_per_day_in_date_order(self):
        response = self.client.get(reverse("portal:schedule_all", kwargs={
            "customer": "test-trip", "access_key": self.days[0].gist_id,
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<article class="schedule-day"', count=3)
        content = response.content.decode()
        self.assertLess(content.index("Run on day 21."), content.index("Run on day 22."))
        self.assertLess(content.index("Run on day 22."), content.index("Run on day 23."))
        self.assertNotContains(response, "Customer work report")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_invalid_or_cross_trip_keys_do_not_fetch_gists(self):
        paths = [
            "/schedule/test-trip/not-a-registered-gist",
            f"/schedule/other-trip/{self.days[0].gist_id}",
            f"/schedule/test-trip/{self.regular.gist_id}",
            f"/schedule/test-trip/all/{self.regular.gist_id}",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)
        self.loader.assert_not_called()

    def test_root_does_not_list_trips_or_fetch_gists(self):
        response = self.client.get("/schedule/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test trip")
        self.assertNotContains(response, self.days[0].gist_id)
        self.loader.assert_not_called()

    def test_day_navigation_reuses_short_lived_gist_cache(self):
        for _ in range(2):
            self.assertEqual(self.client.get(self.days[0].get_absolute_url()).status_code, 200)
        self.loader.assert_called_once()

    def test_missing_gist_does_not_render_a_blank_schedule(self):
        self.loader.side_effect = GistError("Could not load report gist.")
        self.assertEqual(self.client.get(self.days[0].get_absolute_url()).status_code, 404)

    def test_schedule_links_use_new_namespace_and_old_report_links_redirect(self):
        day = self.days[0]
        self.assertEqual(day.get_absolute_url(), f"/schedule/test-trip/{day.gist_id}")
        self.assertRedirects(
            self.client.get(f"/reports/test-trip/{day.gist_id}"),
            day.get_absolute_url(),
            fetch_redirect_response=False,
        )
        self.assertEqual(self.regular.get_absolute_url(), f"/reports/test-trip/{self.regular.gist_id}")
