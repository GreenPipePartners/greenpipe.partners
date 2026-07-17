from django.db import migrations


def update_ignition_price(apps, schema_editor):
    catalog_offer = apps.get_model("panellock", "CatalogOffer")
    catalog_offer.objects.filter(code="ignition-panel-upgrade").update(amount_cents=80000)


def restore_ignition_price(apps, schema_editor):
    catalog_offer = apps.get_model("panellock", "CatalogOffer")
    catalog_offer.objects.filter(code="ignition-panel-upgrade").update(amount_cents=50000)


class Migration(migrations.Migration):
    dependencies = [("panellock", "0009_add_hardware_specifications")]

    operations = [migrations.RunPython(update_ignition_price, restore_ignition_price)]
