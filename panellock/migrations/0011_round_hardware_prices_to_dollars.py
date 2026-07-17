from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from django.db import migrations


def round_hardware_up(apps, schema_editor):
    catalog_offer = apps.get_model("panellock", "CatalogOffer")
    hardware = catalog_offer.objects.filter(category__in=("pc", "panel"), cost_cents__isnull=False)
    for offer in hardware:
        multiplier = Decimal("1") + (offer.markup_percent / Decimal("100"))
        marked_up_dollars = (Decimal(offer.cost_cents) * multiplier / Decimal("100")).quantize(
            Decimal("1"),
            rounding=ROUND_CEILING,
        )
        offer.amount_cents = int(marked_up_dollars * Decimal("100"))
        offer.save(update_fields=["amount_cents"])


def restore_cent_prices(apps, schema_editor):
    catalog_offer = apps.get_model("panellock", "CatalogOffer")
    hardware = catalog_offer.objects.filter(category__in=("pc", "panel"), cost_cents__isnull=False)
    for offer in hardware:
        multiplier = Decimal("1") + (offer.markup_percent / Decimal("100"))
        offer.amount_cents = int(
            (Decimal(offer.cost_cents) * multiplier).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP,
            )
        )
        offer.save(update_fields=["amount_cents"])


class Migration(migrations.Migration):
    dependencies = [("panellock", "0010_update_ignition_conversion_price")]

    operations = [migrations.RunPython(round_hardware_up, restore_cent_prices)]
