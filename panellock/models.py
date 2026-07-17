import hashlib
import re
import secrets
import uuid
from datetime import timedelta
from decimal import Decimal, ROUND_CEILING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from urllib.parse import urlparse

from organizations.models import Organization


class ValidatedModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


def require_same_organization(errors, organization_id, **relations):
    for field, relation in relations.items():
        if relation is not None and relation.organization_id != organization_id:
            errors[field] = "Related object belongs to another organization."


class TimestampedModel(ValidatedModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CatalogOffer(TimestampedModel):
    class Category(models.TextChoices):
        SERVICE = "service", "Service"
        PC = "pc", "PC"
        PANEL = "panel", "Panel"
        LICENSE = "license", "Ignition license"
        SUBSCRIPTION = "subscription", "Subscription"

    class Cadence(models.TextChoices):
        ONCE = "once", "One time"
        ANNUAL = "annual", "Annual"
        CUSTOM = "custom", "Custom quote"

    code = models.SlugField(max_length=80, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    cost_cents = models.PositiveIntegerField(blank=True, null=True)
    amount_cents = models.PositiveIntegerField(blank=True, null=True)
    markup_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    cadence = models.CharField(max_length=12, choices=Cadence.choices, default=Cadence.ONCE)
    external_url = models.URLField(blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    price_checked_at = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category", "sort_order", "name"]

    def clean(self):
        if self.category in {self.Category.PC, self.Category.PANEL} and self.cost_cents is None:
            raise ValidationError({"cost_cents": "Hardware requires a vendor cost."})

    def save(self, *args, **kwargs):
        if self.category in {self.Category.PC, self.Category.PANEL} and self.cost_cents is not None:
            multiplier = Decimal("1") + (Decimal(str(self.markup_percent)) / Decimal("100"))
            marked_up_dollars = (Decimal(self.cost_cents) * multiplier / Decimal("100")).quantize(
                Decimal("1"),
                rounding=ROUND_CEILING,
            )
            self.amount_cents = int(marked_up_dollars * Decimal("100"))
        super().save(*args, **kwargs)

    @property
    def display_price(self):
        if self.amount_cents is None:
            return "Custom quote"
        if self.amount_cents == 0:
            return "$0"
        return f"${self.amount_cents / 100:,.0f}"

    def __str__(self):
        return self.name


class EstimateRequest(TimestampedModel):
    class ProjectType(models.TextChoices):
        CONVERSION = "conversion", "Convert an HMI to Ignition"
        UPGRADE = "upgrade", "Upgrade an existing Ignition panel"
        GATEWAY = "gateway", "Gateway or multi-panel project (custom)"

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        REVIEWING = "reviewing", "Reviewing"
        QUOTED = "quoted", "Quoted"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, blank=True, null=True, related_name="estimates")
    project_type = models.CharField(max_length=16, choices=ProjectType.choices)
    source_platform = models.CharField(max_length=100)
    source_version = models.CharField(max_length=80, blank=True)
    panel_quantity = models.PositiveSmallIntegerField(default=1)
    screen_count = models.PositiveIntegerField(default=0)
    tag_count = models.PositiveIntegerField(default=0)
    driver_count = models.PositiveIntegerField(default=0)
    backup_available = models.BooleanField(default=False)
    requested_timeline = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    contact_name = models.CharField(max_length=120)
    company = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    follow_up_requested = models.BooleanField(default=False)
    one_time_total_cents = models.PositiveIntegerField(default=0)
    annual_total_cents = models.PositiveIntegerField(default=0)
    configuration = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED)
    terms_accepted_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    @property
    def reference(self):
        return f"PL-{str(self.id).split('-')[0].upper()}"

    @property
    def valid_until(self):
        return self.created_at + timedelta(days=30)

    def __str__(self):
        return f"{self.reference} / {self.company}"


class EstimateLine(models.Model):
    estimate = models.ForeignKey(EstimateRequest, on_delete=models.CASCADE, related_name="lines")
    offer = models.ForeignKey(CatalogOffer, on_delete=models.SET_NULL, blank=True, null=True)
    code = models.CharField(max_length=80)
    description = models.CharField(max_length=220)
    quantity = models.PositiveSmallIntegerField()
    unit_amount_cents = models.PositiveIntegerField()
    cadence = models.CharField(max_length=12, choices=CatalogOffer.Cadence.choices)
    source_cost_cents = models.PositiveIntegerField(blank=True, null=True)
    external_url = models.URLField(blank=True)
    price_checked_at = models.DateField(blank=True, null=True)

    @property
    def line_total_cents(self):
        return self.quantity * self.unit_amount_cents


class FollowUpRequest(TimestampedModel):
    estimate = models.OneToOneField(EstimateRequest, on_delete=models.CASCADE, related_name="follow_up")
    preferred_contact = models.CharField(max_length=20, choices=[("email", "Email"), ("phone", "Phone"), ("meeting", "Meeting")])
    best_time = models.CharField(max_length=120, blank=True)
    details = models.TextField(blank=True)


class Site(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="sites")
    name = models.CharField(max_length=160)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.organization} / {self.name}"


class Project(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="panellock_projects")
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, blank=True, null=True, related_name="projects")
    name = models.CharField(max_length=160)
    source_platform = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, default="active")

    def clean(self):
        errors = {}
        require_same_organization(errors, self.organization_id, site=self.site)
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.organization} / {self.name}"


class Panel(TimestampedModel):
    class ReleaseAttention(models.TextChoices):
        CLEAN = "clean", "Clean"
        DUE = "due", "Due"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="panels")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True, related_name="panels")
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, blank=True, null=True, related_name="panels")
    name = models.CharField(max_length=160)
    asset_tag = models.CharField(max_length=80, blank=True)
    ignition_version = models.CharField(max_length=40, blank=True)
    ubuntu_version = models.CharField(max_length=40, blank=True)
    scheduled_update_on = models.DateField(blank=True, null=True)
    last_updated_on = models.DateField(blank=True, null=True)
    release_attention = models.CharField(
        max_length=16,
        choices=ReleaseAttention.choices,
        default=ReleaseAttention.CLEAN,
    )
    certifications = models.JSONField(default=list, blank=True)
    criticality = models.CharField(max_length=20, default="standard")

    def __str__(self):
        return f"{self.organization} / {self.name}"

    def clean(self):
        errors = {}
        require_same_organization(errors, self.organization_id, project=self.project, site=self.site)
        if errors:
            raise ValidationError(errors)

    @property
    def is_update_due(self):
        return (
            self.release_attention == self.ReleaseAttention.DUE
            or bool(self.scheduled_update_on and self.scheduled_update_on <= timezone.localdate())
        )

    @property
    def needs_update_attention(self):
        return self.is_update_due


class PanelAllowance(TimestampedModel):
    class AllowanceType(models.TextChoices):
        COMMUNICATION = "communication", "Communications path"
        APPLICATION = "application", "Application permission"
        NETWORK = "network", "Network access"
        OTHER = "other", "Other"

    panel = models.ForeignKey(Panel, on_delete=models.CASCADE, related_name="allowances")
    allowance_type = models.CharField(max_length=20, choices=AllowanceType.choices)
    name = models.CharField(max_length=160)
    details = models.TextField()
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.panel.name} / {self.name}"


class Device(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending enrollment"
        ACTIVE = "active", "Active"
        SPARE = "spare", "Spare"
        RESERVED = "reserved", "Reserved for replacement"
        LOST = "lost", "Lost"
        RETIRED = "retired", "Retired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="devices")
    name = models.CharField(max_length=160)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    last_seen_at = models.DateTimeField(blank=True, null=True)
    agent_version = models.CharField(max_length=40, blank=True)
    inventory = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.organization} / {self.name}"


class DeviceAssignment(ValidatedModel):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="assignments")
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE, related_name="device_assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["device"], condition=models.Q(ended_at__isnull=True), name="one_active_panel_per_device"),
            models.UniqueConstraint(fields=["panel"], condition=models.Q(ended_at__isnull=True), name="one_active_device_per_panel"),
        ]

    def clean(self):
        if self.device_id and self.panel_id and self.device.organization_id != self.panel.organization_id:
            raise ValidationError({"panel": "Panel belongs to another organization."})


class EnrollmentToken(ValidatedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="enrollment_tokens")
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE, blank=True, null=True, related_name="enrollment_tokens")
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    intended_name = models.CharField(max_length=160)
    as_spare = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def issue(cls, **kwargs):
        token = secrets.token_urlsafe(32)
        obj = cls.objects.create(token_hash=hashlib.sha256(token.encode()).hexdigest(), **kwargs)
        return obj, token

    def clean(self):
        errors = {}
        require_same_organization(errors, self.organization_id, panel=self.panel)
        if self.as_spare and self.panel_id:
            errors["panel"] = "A spare enrollment must remain unassigned."
        if errors:
            raise ValidationError(errors)


class DeviceCredential(ValidatedModel):
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name="credential")
    public_key = models.TextField()
    fingerprint = models.CharField(max_length=64, unique=True)
    revoked_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rotated_at = models.DateTimeField(blank=True, null=True)


class DeviceNonce(ValidatedModel):
    credential = models.ForeignKey(DeviceCredential, on_delete=models.CASCADE, related_name="nonces")
    nonce = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["credential", "nonce"], name="unique_device_nonce")]


class BackupAsset(TimestampedModel):
    class ScanStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        CLEAN = "clean", "Clean"
        QUARANTINED = "quarantined", "Quarantined"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="backups")
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE, related_name="backups")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    original_filename = models.CharField(max_length=255)
    object_key = models.CharField(max_length=500, unique=True)
    size_bytes = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64, blank=True)
    scan_status = models.CharField(max_length=16, choices=ScanStatus.choices, default=ScanStatus.PENDING)
    retention_until = models.DateField()
    pre_update = models.BooleanField(default=False)

    def clean(self):
        errors = {}
        require_same_organization(errors, self.organization_id, panel=self.panel)
        if errors:
            raise ValidationError(errors)


class ManagedCoverage(TimestampedModel):
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE, related_name="coverage_records")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, default="active")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["panel"], condition=models.Q(status="active"), name="one_active_coverage_per_panel")]


class UpdateRelease(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    version = models.CharField(max_length=80)
    severity = models.CharField(max_length=20, default="routine")
    release_notes = models.TextField()
    compatibility = models.JSONField(default=dict, blank=True)
    artifact_url = models.URLField(blank=True)
    artifact_sha256 = models.CharField(max_length=64, blank=True)
    published_at = models.DateTimeField(blank=True, null=True)

    def clean(self):
        errors = {}
        if self.published_at and (not self.artifact_url or not self.artifact_sha256):
            errors["published_at"] = "Published releases require an artifact URL and SHA-256."
        if self.artifact_url and urlparse(self.artifact_url).scheme != "https":
            errors["artifact_url"] = "Update artifacts require HTTPS."
        if self.artifact_sha256 and not re.fullmatch(r"[0-9a-f]{64}", self.artifact_sha256):
            errors["artifact_sha256"] = "Enter a lowercase SHA-256 digest."
        if errors:
            raise ValidationError(errors)


class UpdateNotice(TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="update_notices")
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE, related_name="update_notices")
    release = models.ForeignKey(UpdateRelease, on_delete=models.CASCADE, related_name="notices")
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["panel", "release"], name="unique_panel_release_notice")]

    def clean(self):
        errors = {}
        require_same_organization(errors, self.organization_id, panel=self.panel)
        if errors:
            raise ValidationError(errors)


class UpdateRequest(TimestampedModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        NEEDS_INFO = "needs_info", "Needs information"
        APPROVED = "approved", "Approved"
        SCHEDULED = "scheduled", "Scheduled"
        PRECHECK = "precheck", "Precheck"
        IN_PROGRESS = "in_progress", "In progress"
        VERIFYING = "verifying", "Verifying"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        ROLLED_BACK = "rolled_back", "Rolled back"
        CANCELED = "canceled", "Canceled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="update_requests")
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE, related_name="update_requests")
    release = models.ForeignKey(UpdateRelease, on_delete=models.PROTECT, related_name="update_requests")
    backup = models.ForeignKey(BackupAsset, on_delete=models.PROTECT, blank=True, null=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_updates")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    maintenance_window = models.DateTimeField(blank=True, null=True)
    downtime_acknowledged_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)

    def clean(self):
        errors = {}
        require_same_organization(errors, self.organization_id, panel=self.panel, backup=self.backup)
        if self.backup_id and self.panel_id and self.backup.panel_id != self.panel_id:
            errors["backup"] = "Backup belongs to another panel."
        if errors:
            raise ValidationError(errors)


class ProvisioningPlan(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="provisioning_plans")
    update_request = models.ForeignKey(UpdateRequest, on_delete=models.CASCADE, related_name="plans")
    device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name="plans")
    version = models.PositiveIntegerField(default=1)
    request_text = models.TextField(blank=True)
    operations = models.JSONField(default=list)
    operations_sha256 = models.CharField(max_length=64)
    status = models.CharField(max_length=20, default="draft")
    approved_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["update_request", "version"], name="unique_update_plan_version")]

    def clean(self):
        from .workflow import validate_operations

        validate_operations(self.operations)
        errors = {}
        require_same_organization(errors, self.organization_id, update_request=self.update_request, device=self.device)
        restore_operations = [operation for operation in self.operations if operation.get("type") == "restore_approved_backup"]
        if restore_operations:
            backup = self.update_request.backup
            if not backup:
                errors["operations"] = "A restore plan requires an approved backup."
            elif restore_operations[0]["backup_id"] != str(backup.id):
                errors["operations"] = "Restore operation must use the update request backup."
            elif backup.scan_status != BackupAsset.ScanStatus.CLEAN:
                errors["operations"] = "Restore operation requires a clean backup."
            elif backup.panel_id != self.update_request.panel_id:
                errors["operations"] = "Restore backup belongs to another panel."
        if errors:
            raise ValidationError(errors)


class PlanApproval(ValidatedModel):
    plan = models.ForeignKey(ProvisioningPlan, on_delete=models.CASCADE, related_name="approvals")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    operations_sha256 = models.CharField(max_length=64)
    approved_at = models.DateTimeField(auto_now_add=True)


class UpdateJob(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="update_jobs")
    plan = models.OneToOneField(ProvisioningPlan, on_delete=models.PROTECT, related_name="job")
    device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name="jobs")
    status = models.CharField(max_length=20, default="queued")
    claimed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["device"],
                condition=models.Q(status__in=["queued", "claimed", "in_progress"]),
                name="one_active_update_job_per_device",
            )
        ]

    def clean(self):
        errors = {}
        require_same_organization(errors, self.organization_id, plan=self.plan, device=self.device)
        if self.plan_id and self.device_id and self.plan.device_id != self.device_id:
            errors["device"] = "Job device does not match the approved plan."
        if errors:
            raise ValidationError(errors)


class UpdateEvent(ValidatedModel):
    job = models.ForeignKey(UpdateJob, on_delete=models.CASCADE, related_name="events")
    sequence = models.PositiveIntegerField()
    event_type = models.CharField(max_length=80)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["job", "sequence"], name="unique_job_event_sequence")]
        ordering = ["sequence"]


class AuditEvent(ValidatedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="audit_events")
    actor_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    actor_device = models.ForeignKey(Device, on_delete=models.SET_NULL, blank=True, null=True)
    action = models.CharField(max_length=120)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        errors = {}
        require_same_organization(errors, self.organization_id, actor_device=self.actor_device)
        if errors:
            raise ValidationError(errors)
