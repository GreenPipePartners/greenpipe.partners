from decimal import Decimal

from django.db import migrations


def add_preexisting_panel(apps, schema_editor):
    catalog_offer = apps.get_model("panellock", "CatalogOffer")
    catalog_offer.objects.update_or_create(
        code="panel-existing",
        defaults={
            "category": "panel",
            "name": "Pre-existing panel",
            "description": "Customer supplies a compatible existing panel display.",
            "cost_cents": 0,
            "amount_cents": 0,
            "markup_percent": Decimal("0"),
            "specifications": {
                "Hardware": "Customer supplied",
                "Compatibility": "Reviewed before quote acceptance",
                "Reuse scope": "Existing panel display",
            },
            "cadence": "once",
            "sort_order": 50,
            "is_active": True,
        },
    )


def remove_preexisting_panel(apps, schema_editor):
    catalog_offer = apps.get_model("panellock", "CatalogOffer")
    catalog_offer.objects.filter(code="panel-existing").delete()


class Migration(migrations.Migration):
    dependencies = [("panellock", "0007_update_panellock_protect")]

    operations = [migrations.RunPython(add_preexisting_panel, remove_preexisting_panel)]
