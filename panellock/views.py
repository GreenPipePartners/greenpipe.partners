import json
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core import signing
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from organizations.models import Membership, Organization
from organizations.services import require_membership

from .catalog import (
    IGNITION_SOURCE_CONVERSION_CENTS,
    OTHER_SOURCE_CONVERSION_CENTS,
    SOURCE_PLATFORM_GROUPS,
)
from .forms import EnrollmentForm, FollowUpForm, ManagedUpdateForm
from .models import (
    BackupAsset,
    CatalogOffer,
    EnrollmentToken,
    EstimateRequest,
    Panel,
    PanelAllowance,
    Project,
    ProvisioningPlan,
    UpdateRequest,
)
from .pricing import create_builder_estimate
from .storage import create_upload
from .workflow import approve_plan, operations_digest


@require_GET
def index(request):
    active_hardware = CatalogOffer.objects.filter(is_active=True)
    panel_licenses = active_hardware.filter(
        category=CatalogOffer.Category.LICENSE,
        code__in=["license-existing", "license-edge-panel"],
    ).order_by("sort_order", "name")
    return render(request, "panellock/index.html", {
        "source_platform_groups": SOURCE_PLATFORM_GROUPS,
        "ignition_source_conversion_cents": IGNITION_SOURCE_CONVERSION_CENTS,
        "other_source_conversion_cents": OTHER_SOURCE_CONVERSION_CENTS,
        "pcs": active_hardware.filter(category=CatalogOffer.Category.PC),
        "screens": active_hardware.filter(category=CatalogOffer.Category.PANEL),
        "panel_licenses": panel_licenses,
        "protect_offer": active_hardware.get(code="managed-panel"),
    })


@require_POST
def builder_proposal(request):
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValidationError("The proposal request is malformed.")
        estimate = create_builder_estimate(payload)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "The proposal request is not valid JSON."}, status=400)
    except ValidationError as exc:
        return JsonResponse({"error": " ".join(exc.messages)}, status=400)

    token = _proposal_token(estimate)
    proposal_url = reverse("panellock:proposal", args=[estimate.id, token])
    send_mail(
        f"PanelLock budgetary proposal {estimate.reference}",
        f"{estimate.company} generated {estimate.reference} for {estimate.configuration['project']}. Review it in Django admin.",
        settings.DEFAULT_FROM_EMAIL,
        [settings.PANELLOCK_SALES_EMAIL],
        fail_silently=True,
    )
    return JsonResponse({
        "reference": estimate.reference,
        "proposal_url": proposal_url,
        "one_time_total_cents": estimate.one_time_total_cents,
        "annual_total_cents": estimate.annual_total_cents,
        "valid_until": estimate.valid_until.date().isoformat(),
        "configuration": estimate.configuration,
        "lines": [
            {
                "description": line.description,
                "quantity": line.quantity,
                "unit_amount_cents": line.unit_amount_cents,
                "line_total_cents": line.line_total_cents,
                "cadence": line.cadence,
            }
            for line in estimate.lines.all()
        ],
    }, status=201)


def protect(request):
    protect_offer = get_object_or_404(CatalogOffer, code="managed-panel", is_active=True)
    return render(request, "panellock/protect.html", {"protect_offer": protect_offer})


def _proposal_token(estimate):
    return signing.TimestampSigner(salt="panellock-proposal").sign(str(estimate.id))


def _public_estimate(estimate_id, token):
    try:
        signed_id = signing.TimestampSigner(salt="panellock-proposal").unsign(token, max_age=60 * 60 * 24 * 30)
    except signing.BadSignature as exc:
        raise Http404("Proposal link is invalid or expired.") from exc
    if signed_id != str(estimate_id):
        raise Http404("Proposal link is invalid or expired.")
    return get_object_or_404(EstimateRequest.objects.prefetch_related("lines"), pk=estimate_id)


def proposal(request, estimate_id, token):
    estimate = _public_estimate(estimate_id, token)
    return render(request, "panellock/proposal.html", {"estimate": estimate, "proposal_token": token})


def follow_up(request, estimate_id, token):
    estimate = _public_estimate(estimate_id, token)
    if hasattr(estimate, "follow_up"):
        return render(request, "panellock/follow_up_complete.html", {"estimate": estimate, "proposal_token": token})
    form = FollowUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        follow_up_request = form.save(commit=False)
        follow_up_request.estimate = estimate
        follow_up_request.save()
        estimate.follow_up_requested = True
        estimate.save(update_fields=["follow_up_requested", "updated_at"])
        send_mail(
            f"Follow up requested for {estimate.reference}",
            f"{estimate.contact_name} at {estimate.company} requested {follow_up_request.get_preferred_contact_display()} follow-up.\n\n{follow_up_request.details}",
            settings.DEFAULT_FROM_EMAIL,
            [settings.PANELLOCK_SALES_EMAIL, estimate.email],
            fail_silently=True,
        )
        return redirect("panellock:follow_up", estimate_id=estimate.id, token=token)
    return render(request, "panellock/follow_up.html", {"estimate": estimate, "form": form, "proposal_token": token})


@login_required
def portal(request):
    memberships = request.user.organization_memberships.select_related("organization")
    return render(request, "panellock/portal.html", {"memberships": memberships})


@login_required
def organization_portal(request, organization_slug):
    organization = get_object_or_404(Organization, slug=organization_slug)
    membership = require_membership(request.user, organization)
    panels = list(
        organization.panels.select_related("site", "project")
        .prefetch_related("allowances")
        .order_by("name")
    )
    return render(request, "panellock/organization_portal.html", {
        "organization": organization,
        "membership": membership,
        "panels": panels,
        "devices": organization.devices.order_by("name"),
        "due_count": sum(panel.is_update_due for panel in panels),
    })


@login_required
def panel_allowances(request, organization_slug, panel_id):
    organization = get_object_or_404(Organization, slug=organization_slug)
    membership = require_membership(request.user, organization)
    panel = get_object_or_404(
        Panel.objects.select_related("project").prefetch_related("allowances"),
        pk=panel_id,
        organization=organization,
    )
    allowances = PanelAllowance.objects.filter(panel=panel, is_active=True)
    return render(request, "panellock/panel_allowances.html", {
        "organization": organization,
        "membership": membership,
        "panel": panel,
        "allowances": allowances,
    })


@login_required
def gateway_upload(request, organization_slug, project_id):
    organization = get_object_or_404(Organization, slug=organization_slug)
    membership = require_membership(request.user, organization, Membership.Role.MAINTAINER)
    project = get_object_or_404(Project, pk=project_id, organization=organization)
    panels = organization.panels.select_related("project").order_by("project__name", "name")
    return render(request, "panellock/gateway_upload.html", {
        "organization": organization,
        "membership": membership,
        "project": project,
        "panels": panels,
        "selected_panel_id": panels.filter(project=project).values_list("id", flat=True).first(),
    })


@login_required
def panel_connection(request, organization_slug, panel_id):
    organization = get_object_or_404(Organization, slug=organization_slug)
    membership = require_membership(request.user, organization, Membership.Role.MAINTAINER)
    panel = get_object_or_404(
        Panel.objects.select_related("project"),
        pk=panel_id,
        organization=organization,
    )
    assignment = panel.device_assignments.select_related("device").filter(ended_at__isnull=True).first()
    portal_url = request.build_absolute_uri("/").rstrip("/")
    connection_command = None
    if request.method == "POST":
        if assignment:
            messages.error(request, f"{panel.name} is already connected to {assignment.device.name}.")
        else:
            _, token = EnrollmentToken.issue(
                organization=organization,
                panel=panel,
                intended_name=f"AgentLab for {panel.name}",
                as_spare=False,
                expires_at=timezone.now() + timedelta(hours=1),
                created_by=request.user,
            )
            connection_command = f"sudo panellock-agent connect --portal {portal_url} --token {token}"
            messages.success(request, "One-use AgentLab connection command created. It expires in one hour.")
    return render(request, "panellock/panel_connection.html", {
        "organization": organization,
        "membership": membership,
        "panel": panel,
        "assignment": assignment,
        "portal_url": portal_url,
        "connection_command": connection_command,
    })


@login_required
def upload_session(request, organization_slug):
    if request.method != "POST":
        raise Http404
    organization = get_object_or_404(Organization, slug=organization_slug)
    require_membership(request.user, organization, Membership.Role.MAINTAINER)
    try:
        payload = json.loads(request.body)
        panel = Panel.objects.get(pk=payload["panel_id"], organization=organization)
        result = create_upload(
            organization=organization,
            panel=panel,
            user=request.user,
            filename=payload["filename"],
            size_bytes=int(payload["size_bytes"]),
            sha256=payload["sha256"],
        )
    except (ValueError, KeyError, Panel.DoesNotExist) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(result, status=201)


@login_required
def create_enrollment(request, organization_slug):
    organization = get_object_or_404(Organization, slug=organization_slug)
    require_membership(request.user, organization, Membership.Role.MAINTAINER)
    form = EnrollmentForm(request.POST or None, organization=organization)
    token = None
    if request.method == "POST" and form.is_valid():
        enrollment, token = EnrollmentToken.issue(
            organization=organization,
            panel=form.cleaned_data["panel"],
            intended_name=form.cleaned_data["intended_name"],
            as_spare=form.cleaned_data["as_spare"],
            expires_at=timezone.now() + timedelta(hours=1),
            created_by=request.user,
        )
        messages.success(request, "Enrollment token created. It is shown once and expires in one hour.")
    return render(request, "panellock/enrollment.html", {"organization": organization, "form": form, "token": token})


@login_required
def managed_update(request, organization_slug):
    organization = get_object_or_404(Organization, slug=organization_slug)
    require_membership(request.user, organization, Membership.Role.MAINTAINER)
    form = ManagedUpdateForm(request.POST or None, organization=organization)
    if request.method == "POST" and form.is_valid():
        panel = form.cleaned_data["panel"]
        assignment = panel.device_assignments.select_related("device").filter(ended_at__isnull=True).first()
        target_device = form.cleaned_data["replacement_device"] if form.cleaned_data["replacement"] else (assignment.device if assignment else None)
        if not target_device:
            form.add_error("panel", "This panel has no connected AgentLab.")
        else:
            with transaction.atomic():
                target_device = organization.devices.select_for_update().get(pk=target_device.pk)
                if form.cleaned_data["replacement"] and (
                    target_device.status != target_device.Status.SPARE
                    or target_device.assignments.filter(ended_at__isnull=True).exists()
                ):
                    form.add_error("replacement_device", "That spare is already reserved or assigned.")
                    return render(request, "panellock/managed_update.html", {"organization": organization, "form": form})
                if form.cleaned_data["replacement"]:
                    target_device.status = target_device.Status.RESERVED
                    target_device.save(update_fields=["status", "updated_at"])
                update = UpdateRequest.objects.create(
                    organization=organization,
                    panel=panel,
                    release=form.cleaned_data["release"],
                    backup=form.cleaned_data["backup"],
                    requested_by=request.user,
                    maintenance_window=form.cleaned_data["maintenance_window"],
                    downtime_acknowledged_at=timezone.now(),
                    notes=form.cleaned_data["request_text"],
                )
                operations = [{"type": "verify_prerequisites"}]
                if form.cleaned_data["replacement"]:
                    operations.append({"type": "restore_approved_backup", "backup_id": str(update.backup_id)})
                operations.extend([
                    {"type": "download_signed_artifact", "url": update.release.artifact_url, "sha256": update.release.artifact_sha256},
                    {"type": "install_signed_package", "sha256": update.release.artifact_sha256},
                    {"type": "restart_named_service", "service": "ignition"},
                    {"type": "run_health_check", "profile": "ignition-panel"},
                    {"type": "rollback", "on_failure": True},
                ])
                plan = ProvisioningPlan.objects.create(
                    organization=organization,
                    update_request=update,
                    device=target_device,
                    request_text=form.cleaned_data["request_text"],
                    operations=operations,
                    operations_sha256=operations_digest(operations),
                    expires_at=timezone.now() + timedelta(hours=24),
                )
            return redirect("panellock:review_plan", organization_slug=organization.slug, plan_id=plan.id)
    return render(request, "panellock/managed_update.html", {"organization": organization, "form": form})


@login_required
def review_plan(request, organization_slug, plan_id):
    organization = get_object_or_404(Organization, slug=organization_slug)
    require_membership(request.user, organization, Membership.Role.MAINTAINER)
    plan = get_object_or_404(ProvisioningPlan.objects.select_related("update_request", "device"), pk=plan_id, organization=organization)
    if request.method == "POST":
        if request.POST.get("approve") != "yes":
            messages.error(request, "You must explicitly approve the immutable plan.")
        elif plan.status != "draft":
            messages.info(request, "This plan is no longer awaiting approval.")
        else:
            try:
                approve_plan(plan, request.user)
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))
            else:
                messages.success(request, "Plan approved and queued for the enrolled device.")
                return redirect("panellock:organization_portal", organization_slug=organization.slug)
    return render(request, "panellock/review_plan.html", {"organization": organization, "plan": plan})
