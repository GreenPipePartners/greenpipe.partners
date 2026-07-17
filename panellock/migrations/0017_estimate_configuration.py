from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("panellock", "0016_reduce_pc_markup_to_thirty")]

    operations = [
        migrations.AddField(
            model_name="estimaterequest",
            name="configuration",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
