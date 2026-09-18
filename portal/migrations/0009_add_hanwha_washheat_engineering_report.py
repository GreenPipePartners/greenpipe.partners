from django.db import migrations


GIST_ID = "e0b8e388d5adbe939b6f2ab8895d9426"


def add_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.update_or_create(
        customer="Hanwha",
        gist_id=GIST_ID,
        defaults={
            "customer_name": "Edward Wingrove",
            "report_type": "engineering",
            "title": "WashHeat Automation — Revision O",
            "gist_url": f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        },
    )


def remove_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.filter(customer="Hanwha", gist_id=GIST_ID).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0008_add_weekly_reports_20260907"),
    ]

    operations = [
        migrations.RunPython(add_report, remove_report),
    ]
