from datetime import date

from django.db import migrations


GIST_ID = "fceff971eeceef080dd0e5e074b3d1e2"


def add_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.update_or_create(
        customer="Hanwha",
        gist_id=GIST_ID,
        defaults={
            "customer_name": "Jermyn Chester",
            "report_type": "weekly",
            "title": "Weekly Work Report",
            "start_date": date(2026, 10, 10),
            "end_date": date(2026, 10, 11),
            "gist_url": f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        },
    )


def remove_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.filter(customer="Hanwha", gist_id=GIST_ID).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0014_add_purewest_weekly_report_20261005"),
    ]

    operations = [
        migrations.RunPython(add_report, remove_report),
    ]
