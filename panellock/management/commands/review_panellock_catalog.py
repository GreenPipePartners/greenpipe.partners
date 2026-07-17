from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from panellock.models import CatalogOffer


class Command(BaseCommand):
    help = "Notify staff when externally priced PanelLock catalog entries need review."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **options):
        cutoff = timezone.localdate() - timedelta(days=options["days"])
        stale = CatalogOffer.objects.filter(is_active=True, external_url__gt="").filter(
            price_checked_at__lt=cutoff
        ) | CatalogOffer.objects.filter(is_active=True, external_url__gt="", price_checked_at__isnull=True)
        stale = stale.distinct().order_by("category", "name")
        if not stale:
            self.stdout.write(self.style.SUCCESS("PanelLock external prices are current."))
            return
        lines = [f"{offer.name}: {offer.external_url} (last checked {offer.price_checked_at or 'never'})" for offer in stale]
        send_mail(
            "PanelLock catalog price review required",
            "Review these external prices and update cost/list price plus price_checked_at:\n\n" + "\n".join(lines),
            settings.DEFAULT_FROM_EMAIL,
            [settings.PANELLOCK_SALES_EMAIL],
            fail_silently=False,
        )
        self.stdout.write(self.style.WARNING(f"Sent review notice for {len(lines)} catalog entries."))
