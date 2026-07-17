from datetime import date

from django.db import migrations


EDGE_FEATURES = {
    "edge_iiot": "Includes everything in Edge IIoT",
    "development": "Get powerful development tools for building edge-ready HMIs",
    "visualization": "Visualize real-time data at the edge",
    "history": "Store tag history data for up to 35 days if connection is lost",
}


def update_licenses(apps, schema_editor):
    CatalogOffer = apps.get_model("panellock", "CatalogOffer")
    CatalogOffer.objects.filter(code="license-existing").update(
        name="Purchase Ignition Separately",
        description="Customer purchases or supplies compatible Ignition licensing separately.",
    )
    CatalogOffer.objects.filter(code="license-edge-panel").update(
        name="Ignition Edge Panel",
        description="For visualization of data & control of processes at the network's edge.",
        amount_cents=195000,
        specifications=EDGE_FEATURES,
        price_checked_at=date(2026, 7, 16),
    )


def restore_licenses(apps, schema_editor):
    CatalogOffer = apps.get_model("panellock", "CatalogOffer")
    CatalogOffer.objects.filter(code="license-existing").update(
        name="Use existing Ignition license",
        description="Customer supplies a compatible license.",
    )
    CatalogOffer.objects.filter(code="license-edge-panel").update(
        name="Ignition Edge Panel - manufacturer list price",
        description="Perpetual Edge Panel license with limited Vision or Perspective visualization.",
        specifications={},
    )


class Migration(migrations.Migration):
    dependencies = [("panellock", "0013_release_attention_due")]

    operations = [migrations.RunPython(update_licenses, restore_licenses)]
