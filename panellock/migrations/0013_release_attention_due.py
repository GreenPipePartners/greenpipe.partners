from django.db import migrations, models


def critical_to_due(apps, schema_editor):
    Panel = apps.get_model("panellock", "Panel")
    Panel.objects.filter(release_attention="critical").update(release_attention="due")


def due_to_critical(apps, schema_editor):
    Panel = apps.get_model("panellock", "Panel")
    Panel.objects.filter(release_attention="due").update(release_attention="critical")


class Migration(migrations.Migration):
    dependencies = [("panellock", "0012_panel_inventory_and_allowances")]

    operations = [
        migrations.RunPython(critical_to_due, due_to_critical),
        migrations.AlterField(
            model_name="panel",
            name="release_attention",
            field=models.CharField(
                choices=[("clean", "Clean"), ("due", "Due")],
                default="clean",
                max_length=16,
            ),
        ),
    ]
