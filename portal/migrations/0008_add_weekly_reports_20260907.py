from datetime import date

from django.db import migrations


REPORTS = (
    {
        "customer": "Hanwha",
        "customer_name": "Edward Wingrove",
        "gist_id": "991f2b2b186fb837e625e7f06c3b050d",
        "start_date": date(2026, 9, 11),
        "end_date": date(2026, 9, 11),
    },
    {
        "customer": "Magnolia",
        "customer_name": "Riley Houston & Jarod Beekman",
        "gist_id": "969bf6b192d8166d0815f52235d65707",
        "start_date": date(2026, 9, 10),
        "end_date": date(2026, 9, 10),
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
        ("portal", "0007_add_hanwha_magnolia_weekly_reports"),
    ]

    operations = [
        migrations.RunPython(add_reports, remove_reports),
    ]
