from datetime import date

from django.db import migrations


GIST_ID = "a7cd90b982f51e8c568a232d8c5b491e"


def add_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.update_or_create(
        customer="PureWest",
        gist_id=GIST_ID,
        defaults={
            "customer_name": "Johnny Ortega",
            "report_type": "weekly",
            "title": "Weekly Work Report",
            "start_date": date(2026, 11, 3),
            "end_date": date(2026, 11, 3),
            "gist_url": f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        },
    )


def remove_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.filter(customer="PureWest", gist_id=GIST_ID).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0018_add_hanwha_weekly_report_20261102"),
    ]

    operations = [
        migrations.RunPython(add_report, remove_report),
    ]
