import hashlib
import json
import re
import uuid
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import PlanApproval, ProvisioningPlan, UpdateJob


OPERATION_KEYS = {
    "verify_prerequisites": {"type"},
    "download_signed_artifact": {"type", "url", "sha256"},
    "install_signed_package": {"type", "sha256"},
    "restore_approved_backup": {"type", "backup_id"},
    "apply_known_configuration": {"type", "profile"},
    "restart_named_service": {"type", "service"},
    "run_health_check": {"type", "profile"},
    "rollback": {"type", "on_failure"},
}


def canonical_operations(operations):
    return json.dumps(operations, sort_keys=True, separators=(",", ":")).encode()


def operations_digest(operations):
    return hashlib.sha256(canonical_operations(operations)).hexdigest()


def validate_operations(operations):
    if not isinstance(operations, list) or not operations:
        raise ValidationError({"operations": "A plan needs at least one typed operation."})
    for operation in operations:
        if not isinstance(operation, dict) or operation.get("type") not in OPERATION_KEYS:
            raise ValidationError({"operations": "Plan contains a forbidden operation."})
        operation_type = operation["type"]
        if set(operation) != OPERATION_KEYS[operation_type]:
            raise ValidationError({"operations": f"{operation_type} has invalid parameters."})
        if any(isinstance(value, (dict, list)) for value in operation.values()):
            raise ValidationError({"operations": "Nested operation parameters are forbidden."})
        if operation_type == "download_signed_artifact":
            parsed = urlparse(operation["url"])
            if parsed.scheme != "https" or not parsed.netloc or not re.fullmatch(r"[0-9a-f]{64}", operation["sha256"]):
                raise ValidationError({"operations": "Artifact URL or SHA-256 is invalid."})
        elif operation_type == "install_signed_package" and not re.fullmatch(r"[0-9a-f]{64}", operation["sha256"]):
            raise ValidationError({"operations": "Package SHA-256 is invalid."})
        elif operation_type == "restore_approved_backup":
            try:
                uuid.UUID(operation["backup_id"])
            except (ValueError, TypeError):
                raise ValidationError({"operations": "Backup ID is invalid."})
        elif operation_type == "restart_named_service" and operation["service"] != "ignition":
            raise ValidationError({"operations": "Only the Ignition service may be restarted."})
        elif operation_type in {"apply_known_configuration", "run_health_check"} and operation["profile"] not in {"ignition-panel"}:
            raise ValidationError({"operations": "Configuration profile is not allowlisted."})
        elif operation_type == "rollback" and operation["on_failure"] is not True:
            raise ValidationError({"operations": "Rollback may only be configured as an on-failure guard."})


@transaction.atomic
def approve_plan(plan, user):
    plan = ProvisioningPlan.objects.select_for_update().get(pk=plan.pk)
    plan.device.__class__.objects.select_for_update().get(pk=plan.device_id)
    plan.full_clean()
    digest = operations_digest(plan.operations)
    if digest != plan.operations_sha256:
        raise ValidationError("Plan changed after it was generated.")
    PlanApproval.objects.create(plan=plan, approved_by=user, operations_sha256=digest)
    plan.status = "approved"
    plan.approved_at = timezone.now()
    plan.save(update_fields=["status", "approved_at", "updated_at"])
    if UpdateJob.objects.filter(device=plan.device, status__in=["queued", "claimed", "in_progress"]).exists():
        raise ValidationError("This device already has an active update job.")
    try:
        with transaction.atomic():
            return UpdateJob.objects.create(organization=plan.organization, plan=plan, device=plan.device)
    except IntegrityError as exc:
        raise ValidationError("This device already has an active update job.") from exc
