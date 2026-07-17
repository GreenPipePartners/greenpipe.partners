from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from panellock.models import Device, ProvisioningPlan, UpdateRequest


class Command(BaseCommand):
    help = "Expire abandoned PanelLock plans and release reserved spare devices."

    def handle(self, *args, **options):
        expired_count = 0
        plan_ids = ProvisioningPlan.objects.filter(
            status__in=["draft", "approved"],
            expires_at__lte=timezone.now(),
        ).values_list("pk", flat=True)
        for plan_id in plan_ids:
            with transaction.atomic():
                plan = ProvisioningPlan.objects.select_for_update().select_related("device", "update_request").get(pk=plan_id)
                if plan.status not in {"draft", "approved"} or not plan.expires_at or plan.expires_at > timezone.now():
                    continue
                if hasattr(plan, "job") and plan.job.status == "in_progress":
                    continue
                plan.status = "expired"
                ProvisioningPlan.objects.filter(pk=plan.pk).update(status="expired", updated_at=timezone.now())
                if hasattr(plan, "job") and plan.job.status in {"queued", "claimed"}:
                    plan.job.status = "canceled"
                    plan.job.completed_at = timezone.now()
                    plan.job.save(update_fields=["status", "completed_at", "updated_at"])
                if plan.update_request.status not in {
                    UpdateRequest.Status.COMPLETED,
                    UpdateRequest.Status.FAILED,
                    UpdateRequest.Status.ROLLED_BACK,
                    UpdateRequest.Status.CANCELED,
                }:
                    plan.update_request.status = UpdateRequest.Status.CANCELED
                    plan.update_request.save(update_fields=["status", "updated_at"])
                if plan.device.status == Device.Status.RESERVED:
                    plan.device.status = Device.Status.SPARE
                    plan.device.save(update_fields=["status", "updated_at"])
                expired_count += 1
        self.stdout.write(self.style.SUCCESS(f"Expired {expired_count} PanelLock plan(s)."))
