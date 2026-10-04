from datetime import date

from django.db import migrations


GIST_ID = "3337b3e6c90af565a70136a689384c0f"


def add_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.update_or_create(
        customer="PureWest",
        gist_id=GIST_ID,
        defaults={
            "customer_name": "Johnny Ortega",
            "report_type": "weekly",
            "title": "Weekly Work Report",
            "start_date": date(2026, 9, 29),
            "end_date": date(2026, 10, 2),
            "gist_url": f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        },
    )


def remove_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.filter(customer="PureWest", gist_id=GIST_ID).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0012_add_icc_2026_schedule"),
    ]

    operations = [
        migrations.RunPython(add_report, remove_report),
    ]
