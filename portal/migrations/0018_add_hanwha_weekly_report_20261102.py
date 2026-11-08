from datetime import date

from django.db import migrations


GIST_ID = "4c7af4138f233f84599606b5ab158b15"


def add_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.update_or_create(
        customer="Hanwha",
        gist_id=GIST_ID,
        defaults={
            "customer_name": "Chris Godfrey, Jermyn Chester, and Edward Wingrove",
            "report_type": "weekly",
            "title": "Weekly Work Report",
            "start_date": date(2026, 11, 4),
            "end_date": date(2026, 11, 6),
            "gist_url": f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        },
    )


def remove_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.filter(customer="Hanwha", gist_id=GIST_ID).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0017_add_hanwha_weekly_report_20261026"),
    ]

    operations = [
        migrations.RunPython(add_report, remove_report),
    ]
