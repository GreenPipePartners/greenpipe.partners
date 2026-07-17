from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("panellock", "0011_round_hardware_prices_to_dollars")]

    operations = [
        migrations.AddField(
            model_name="panel",
            name="ubuntu_version",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="panel",
            name="scheduled_update_on",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="panel",
            name="last_updated_on",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="panel",
            name="release_attention",
            field=models.CharField(
                choices=[("clean", "Clean"), ("critical", "Critical")],
                default="clean",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="panel",
            name="certifications",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.CreateModel(
            name="PanelAllowance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "allowance_type",
                    models.CharField(
                        choices=[
                            ("communication", "Communications path"),
                            ("application", "Application permission"),
                            ("network", "Network access"),
                            ("other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("name", models.CharField(max_length=160)),
                ("details", models.TextField()),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                (
                    "panel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="allowances",
                        to="panellock.panel",
                    ),
                ),
            ],
            options={"ordering": ["sort_order", "name"]},
        ),
    ]
