from datetime import date

from django.db import migrations


GIST_ID = "002cc28e23cc145b19ff8a333a3a11ef"


def add_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.update_or_create(
        customer="Magnolia",
        gist_id=GIST_ID,
        defaults={
            "customer_name": "Riley Houston & Jarod Beekman",
            "report_type": "weekly",
            "title": "Weekly Work Report",
            "start_date": date(2026, 7, 22),
            "end_date": date(2026, 7, 24),
            "gist_url": f"https://gist.github.com/Bobby-Miller/{GIST_ID}",
        },
    )


def remove_report(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.filter(customer="Magnolia", gist_id=GIST_ID).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0005_alter_release_topic"),
    ]

    operations = [
        migrations.RunPython(add_report, remove_report),
    ]
