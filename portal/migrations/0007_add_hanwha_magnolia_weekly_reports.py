from datetime import date

from django.db import migrations


REPORTS = (
    {
        "customer": "Hanwha",
        "customer_name": "Edward Wingrove",
        "gist_id": "75a15e8fb83ce5fb68d12e386d64e9a1",
        "start_date": date(2026, 7, 28),
        "end_date": date(2026, 7, 28),
    },
    {
        "customer": "Magnolia",
        "customer_name": "Riley Houston & Jarod Beekman",
        "gist_id": "601a4d2e4903b69b665d4ce38cf97178",
        "start_date": date(2026, 7, 27),
        "end_date": date(2026, 7, 30),
    },
)


def add_reports(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    for report in REPORTS:
        gist_id = report["gist_id"]
        Report.objects.update_or_create(
            customer=report["customer"],
            gist_id=gist_id,
            defaults={
                "customer_name": report["customer_name"],
                "report_type": "weekly",
                "title": "Weekly Work Report",
                "start_date": report["start_date"],
                "end_date": report["end_date"],
                "gist_url": f"https://gist.github.com/Bobby-Miller/{gist_id}",
            },
        )


def remove_reports(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    for report in REPORTS:
        Report.objects.filter(
            customer=report["customer"], gist_id=report["gist_id"]
        ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0006_add_magnolia_weekly_report_20260722"),
    ]

    operations = [
        migrations.RunPython(add_reports, remove_reports),
    ]
