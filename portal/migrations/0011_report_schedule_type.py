from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("portal", "0010_remove_washheat_report_revision_label")]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="report_type",
            field=models.CharField(
                choices=[("weekly", "Weekly"), ("engineering", "Engineering"), ("schedule", "Daily schedule")],
                default="weekly",
                max_length=24,
            ),
        ),
    ]
