import base64
import hashlib
import json
import time
from datetime import timedelta
from functools import wraps

import boto3
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import (
    AuditEvent,
    Device,
    DeviceAssignment,
    DeviceCredential,
    DeviceNonce,
    EnrollmentToken,
    UpdateEvent,
    UpdateJob,
    UpdateRequest,
)


def _json(request):
    return json.loads(request.body or b"{}")


@csrf_exempt
def enroll(request):
    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)
    try:
        payload = _json(request)
        token_hash = hashlib.sha256(payload["token"].encode()).hexdigest()
        public_key_bytes = base64.b64decode(payload["public_key"], validate=True)
        Ed25519PublicKey.from_public_bytes(public_key_bytes)
    except (KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "invalid_enrollment"}, status=400)

    with transaction.atomic():
        enrollment = EnrollmentToken.objects.select_for_update().filter(token_hash=token_hash).first()
        if not enrollment or enrollment.used_at or enrollment.expires_at <= timezone.now():
            return JsonResponse({"error": "invalid_or_expired_token"}, status=403)
        if enrollment.panel and not enrollment.as_spare and enrollment.panel.device_assignments.filter(ended_at__isnull=True).exists():
            return JsonResponse({"error": "panel_already_has_device"}, status=409)
        fingerprint = hashlib.sha256(public_key_bytes).hexdigest()
        if DeviceCredential.objects.filter(fingerprint=fingerprint).exists():
            return JsonResponse({"error": "credential_already_enrolled"}, status=409)
        device = Device.objects.create(
            organization=enrollment.organization,
            name=enrollment.intended_name,
            status=Device.Status.SPARE if enrollment.as_spare else Device.Status.ACTIVE,
            inventory=payload.get("inventory", {}),
            agent_version=payload.get("agent_version", "")[:40],
            last_seen_at=timezone.now(),
        )
        DeviceCredential.objects.create(
            device=device,
            public_key=base64.b64encode(public_key_bytes).decode(),
            fingerprint=fingerprint,
        )
        if enrollment.panel and not enrollment.as_spare:
            DeviceAssignment.objects.create(device=device, panel=enrollment.panel)
        enrollment.used_at = timezone.now()
        enrollment.save(update_fields=["used_at"])
        AuditEvent.objects.create(
            organization=device.organization,
            actor_device=device,
            action="device.enrolled",
            object_type="device",
            object_id=str(device.id),
            metadata={"fingerprint": fingerprint, "inventory_mac_addresses": payload.get("inventory", {}).get("mac_addresses", [])},
        )
    return JsonResponse({"device_id": str(device.id), "fingerprint": fingerprint}, status=201)


def signed_device_view(view):
    @csrf_exempt
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        device_id = request.headers.get("X-PanelLock-Device", "")
        timestamp = request.headers.get("X-PanelLock-Timestamp", "")
        nonce = request.headers.get("X-PanelLock-Nonce", "")
        signature = request.headers.get("X-PanelLock-Signature", "")
        try:
            if not device_id or not nonce or len(nonce) > 80 or not signature:
                raise ValueError
            timestamp_int = int(timestamp)
            if abs(int(time.time()) - timestamp_int) > settings.PANELLOCK_DEVICE_CLOCK_SKEW_SECONDS:
                raise ValueError
            credential = DeviceCredential.objects.select_related("device", "device__organization").get(
                device_id=device_id,
                revoked_at__isnull=True,
                device__status__in=[Device.Status.ACTIVE, Device.Status.SPARE, Device.Status.RESERVED],
            )
            digest = hashlib.sha256(request.body).hexdigest()
            canonical = f"{request.method}\n{request.path}\n{timestamp}\n{nonce}\n{digest}".encode()
            public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(credential.public_key))
            public_key.verify(base64.b64decode(signature, validate=True), canonical)
            DeviceNonce.objects.create(credential=credential, nonce=nonce)
        except (ValueError, ValidationError, DeviceCredential.DoesNotExist, InvalidSignature, IntegrityError):
            return JsonResponse({"error": "invalid_device_signature"}, status=401)
        request.panellock_device = credential.device
        return view(request, *args, **kwargs)

    return wrapped


@signed_device_view
def heartbeat(request):
    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)
    try:
        payload = _json(request)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)
    device = request.panellock_device
    device.last_seen_at = timezone.now()
    device.agent_version = str(payload.get("agent_version", device.agent_version))[:40]
    device.inventory = payload.get("inventory", device.inventory)
    device.save(update_fields=["last_seen_at", "agent_version", "inventory", "updated_at"])
    return JsonResponse({"status": "ok", "server_time": int(time.time())})


def _signed_manifest(job):
    from .workflow import operations_digest

    job.plan.full_clean()
    if operations_digest(job.plan.operations) != job.plan.operations_sha256:
        raise RuntimeError("plan_digest_mismatch")
    manifest = {
        "job_id": str(job.id),
        "device_id": str(job.device_id),
        "plan_id": str(job.plan_id),
        "operations_sha256": job.plan.operations_sha256,
        "operations": job.plan.operations,
        "expires_at": job.plan.expires_at.isoformat() if job.plan.expires_at else None,
    }
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).digest()
    if not settings.PANELLOCK_KMS_KEY_ID:
        raise RuntimeError("manifest_signing_not_configured")
    response = boto3.client("kms", region_name=settings.PANELLOCK_S3_REGION).sign(
        KeyId=settings.PANELLOCK_KMS_KEY_ID,
        Message=digest,
        MessageType="DIGEST",
        SigningAlgorithm="ECDSA_SHA_256",
    )
    manifest["signature"] = base64.b64encode(response["Signature"]).decode()
    manifest["signing_key_id"] = settings.PANELLOCK_KMS_KEY_ID
    return manifest


@signed_device_view
def next_job(request):
    if request.method != "GET":
        return JsonResponse({"error": "method_not_allowed"}, status=405)
    with transaction.atomic():
        retry_before = timezone.now() - timedelta(minutes=1)
        job = UpdateJob.objects.select_for_update().select_related("plan").filter(
            device=request.panellock_device,
            plan__status="approved",
        ).filter(
            Q(status="queued") | Q(status="claimed", claimed_at__lte=retry_before, events__isnull=True)
        ).order_by("created_at").first()
        if not job:
            return JsonResponse({"job": None})
        approval = job.plan.approvals.filter(operations_sha256=job.plan.operations_sha256).exists()
        if not approval or (job.plan.expires_at and job.plan.expires_at <= timezone.now()):
            return JsonResponse({"job": None})
        try:
            manifest = _signed_manifest(job)
        except (RuntimeError, ValidationError) as exc:
            return JsonResponse({"error": str(exc)}, status=503)
        job.status = "claimed"
        job.claimed_at = timezone.now()
        job.save(update_fields=["status", "claimed_at", "updated_at"])
    return JsonResponse({"job": manifest})


@signed_device_view
def job_event(request, job_id):
    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)
    try:
        payload = _json(request)
        sequence = int(payload["sequence"])
        event_type = str(payload["event_type"])[:80]
        event_payload = payload.get("payload", {})
    except (KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "invalid_or_duplicate_event"}, status=409)
    terminal = {"completed", "failed", "rolled_back"}
    with transaction.atomic():
        job = UpdateJob.objects.select_for_update().select_related("plan__update_request__panel").filter(
            pk=job_id,
            device=request.panellock_device,
        ).first()
        if not job:
            return JsonResponse({"error": "job_not_found"}, status=404)
        if job.status in terminal | {"canceled"}:
            return JsonResponse({"error": "job_already_terminal"}, status=409)
        if job.status == "claimed" and event_type != "started":
            return JsonResponse({"error": "job_must_start_before_events"}, status=409)
        if job.status == "in_progress" and event_type == "started":
            return JsonResponse({"error": "job_already_started"}, status=409)
        if job.events.filter(sequence=sequence).exists():
            return JsonResponse({"error": "invalid_or_duplicate_event"}, status=409)
        event = UpdateEvent.objects.create(job=job, sequence=sequence, event_type=event_type, payload=event_payload)
        if event_type == "started":
            job.status = "in_progress"
            job.save(update_fields=["status", "updated_at"])
            job.plan.update_request.status = job.plan.update_request.Status.IN_PROGRESS
            job.plan.update_request.save(update_fields=["status", "updated_at"])
        elif event_type in terminal:
            job.status = event_type
            job.completed_at = timezone.now()
            job.save(update_fields=["status", "completed_at", "updated_at"])
            is_replacement = any(operation.get("type") == "restore_approved_backup" for operation in job.plan.operations)
            panel = job.plan.update_request.panel
            status_map = {
                "completed": job.plan.update_request.Status.COMPLETED,
                "failed": job.plan.update_request.Status.FAILED,
                "rolled_back": job.plan.update_request.Status.ROLLED_BACK,
            }
            job.plan.update_request.status = status_map[event_type]
            job.plan.update_request.save(update_fields=["status", "updated_at"])
            if event_type == "completed" and is_replacement:
                current = panel.device_assignments.select_for_update().filter(ended_at__isnull=True).first()
                if not current or current.device_id != job.device_id:
                    if current:
                        current.ended_at = timezone.now()
                        current.save(update_fields=["ended_at"])
                        current.device.status = Device.Status.RETIRED
                        current.device.save(update_fields=["status", "updated_at"])
                        if hasattr(current.device, "credential"):
                            current.device.credential.revoked_at = timezone.now()
                            current.device.credential.save(update_fields=["revoked_at"])
                        canceled_jobs = UpdateJob.objects.filter(
                            device=current.device,
                            status__in=["queued", "claimed", "in_progress"],
                        )
                        canceled_request_ids = list(canceled_jobs.values_list("plan__update_request_id", flat=True))
                        canceled_jobs.update(
                            status="canceled",
                            completed_at=timezone.now(),
                        )
                        UpdateRequest.objects.filter(pk__in=canceled_request_ids).update(
                            status=UpdateRequest.Status.CANCELED,
                            updated_at=timezone.now(),
                        )
                    DeviceAssignment.objects.create(device=job.device, panel=panel)
                    job.device.status = Device.Status.ACTIVE
                    job.device.save(update_fields=["status", "updated_at"])
                    AuditEvent.objects.create(
                        organization=job.organization,
                        actor_device=job.device,
                        action="panel.device_replaced",
                        object_type="panel",
                        object_id=str(panel.id),
                        metadata={"job_id": str(job.id)},
                    )
            elif is_replacement:
                job.device.status = Device.Status.SPARE
                job.device.save(update_fields=["status", "updated_at"])
    return JsonResponse({"accepted": event.sequence}, status=202)
