from datetime import date

from django.db import migrations


DAYS = (
    (21, "Travel to Sacramento", "2601da996012876446dda39567d1d17e"),
    (22, "Technology + historians", "77d85c6a5325d028d0906f77fd4328a4"),
    (23, "Your Table Talk + sandboxes", "dcf77644e4a5805a159bc1777a88455d"),
    (24, "Oil & gas + operations", "c0c4b8da7ab74e1382809afb37649f0c"),
    (25, "Travel home", "af963f3d7b2d17c96e0be1c1a4825b60"),
)


def add_schedule(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    for number, title, gist_id in DAYS:
        Report.objects.using(schema_editor.connection.alias).update_or_create(
            customer="icc-2026",
            gist_id=gist_id,
            defaults={
                "customer_name": "Sacramento · ICC 2026",
                "report_type": "schedule",
                "title": title,
                "start_date": date(2026, 9, number),
                "end_date": date(2026, 9, number),
                "gist_url": f"https://gist.github.com/Bobby-Miller/{gist_id}",
            },
        )


def remove_schedule(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.using(schema_editor.connection.alias).filter(
        customer="icc-2026",
        report_type="schedule",
        gist_id__in=[day[2] for day in DAYS],
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("portal", "0011_report_schedule_type")]
    operations = [migrations.RunPython(add_schedule, remove_schedule)]
