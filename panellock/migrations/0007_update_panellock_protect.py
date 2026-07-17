from django.db import migrations


def update_protect_offer(apps, schema_editor):
    catalog_offer = apps.get_model("panellock", "CatalogOffer")
    catalog_offer.objects.filter(code="managed-panel").update(
        name="PanelLock Protect",
        description=(
            "Semi-annual update reviews, protected backups, notifications, and "
            "out-of-cycle critical security patches or mitigations."
        ),
        amount_cents=85000,
    )


def restore_previous_offer(apps, schema_editor):
    catalog_offer = apps.get_model("panellock", "CatalogOffer")
    catalog_offer.objects.filter(code="managed-panel").update(
        name="Managed panel coverage",
        description="Managed update reviews, backups, notifications, and guided replacement.",
        amount_cents=50000,
    )


class Migration(migrations.Migration):
    dependencies = [("panellock", "0006_alter_updateevent_payload")]

    operations = [migrations.RunPython(update_protect_offer, restore_previous_offer)]
