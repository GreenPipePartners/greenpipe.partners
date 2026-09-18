from django.db import migrations


GIST_ID = "e0b8e388d5adbe939b6f2ab8895d9426"


def remove_revision_label(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.filter(customer="Hanwha", gist_id=GIST_ID).update(title="WashHeat Automation")


def restore_revision_label(apps, schema_editor):
    Report = apps.get_model("portal", "Report")
    Report.objects.filter(customer="Hanwha", gist_id=GIST_ID).update(title="WashHeat Automation — Revision O")


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0009_add_hanwha_washheat_engineering_report"),
    ]

    operations = [
        migrations.RunPython(remove_revision_label, restore_revision_label),
    ]
