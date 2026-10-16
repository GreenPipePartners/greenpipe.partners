from datetime import date

from django.db import migrations


GIST_ID = "0896e78f0ca6395b105b19c7270d9d4d"


def add_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.update_or_create(
        customer="Hanwha",
        gist_id=GIST_ID,
        defaults={
            "customer_name": "Chris Godfrey, Jermyn Chester, and Edward Wingrove",
            "report_type": "weekly",
            "title": "Weekly Work Report",
            "start_date": date(2026, 10, 12),
            "end_date": date(2026, 10, 16),
            "gist_url": f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        },
    )


def remove_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.filter(customer="Hanwha", gist_id=GIST_ID).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0015_add_hanwha_weekly_report_20261005"),
    ]

    operations = [
        migrations.RunPython(add_report, remove_report),
    ]
