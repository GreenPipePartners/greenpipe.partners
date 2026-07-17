from decimal import Decimal, ROUND_CEILING

from django.db import migrations


def set_pc_markup(apps, markup_percent):
    CatalogOffer = apps.get_model("panellock", "CatalogOffer")
    for offer in CatalogOffer.objects.filter(category="pc", cost_cents__isnull=False):
        multiplier = Decimal("1") + (markup_percent / Decimal("100"))
        marked_up_dollars = (Decimal(offer.cost_cents) * multiplier / Decimal("100")).quantize(
            Decimal("1"),
            rounding=ROUND_CEILING,
        )
        offer.markup_percent = markup_percent
        offer.amount_cents = int(marked_up_dollars * Decimal("100"))
        offer.save(update_fields=["markup_percent", "amount_cents"])


def reduce_pc_markup(apps, schema_editor):
    set_pc_markup(apps, Decimal("30.00"))


def restore_pc_markup(apps, schema_editor):
    set_pc_markup(apps, Decimal("50.00"))


class Migration(migrations.Migration):
    dependencies = [("panellock", "0015_increase_pc_markup")]

    operations = [migrations.RunPython(reduce_pc_markup, restore_pc_markup)]
