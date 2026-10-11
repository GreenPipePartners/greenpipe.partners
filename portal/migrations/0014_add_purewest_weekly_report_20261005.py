from datetime import date

from django.db import migrations


GIST_ID = "3f35a15813ae39973f59a56f4747b062"


def add_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.update_or_create(
        customer="PureWest",
        gist_id=GIST_ID,
        defaults={
            "customer_name": "Johnny Ortega",
            "report_type": "weekly",
            "title": "Weekly Work Report",
            "start_date": date(2026, 10, 7),
            "end_date": date(2026, 10, 7),
            "gist_url": f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        },
    )


def remove_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.filter(customer="PureWest", gist_id=GIST_ID).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0013_add_purewest_weekly_report_20260928"),
    ]

    operations = [
        migrations.RunPython(add_report, remove_report),
    ]
