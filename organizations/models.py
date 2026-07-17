import hashlib
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    class Region(models.TextChoices):
        US_EAST = "us-east", "United States East"
        US_WEST = "us-west", "United States West"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=80, unique=True)
    data_region = models.CharField(max_length=20, choices=Region.choices, default=Region.US_EAST)
    ai_processing_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MAINTAINER = "maintainer", "Maintainer"
        BILLING = "billing", "Billing"
        VIEWER = "viewer", "Viewer"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organization_memberships")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.VIEWER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "user"], name="unique_org_user")]

    def __str__(self):
        return f"{self.organization} / {self.user} / {self.get_role_display()}"


class Invitation(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    role = models.CharField(max_length=16, choices=Membership.Role.choices, default=Membership.Role.VIEWER)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sent_invitations")
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def issue(cls, *, organization, email, role, invited_by, lifetime_hours=72):
        token = secrets.token_urlsafe(32)
        invitation = cls.objects.create(
            organization=organization,
            email=email.lower(),
            role=role,
            invited_by=invited_by,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(hours=lifetime_hours),
        )
        return invitation, token

    @property
    def is_active(self):
        return not self.accepted_at and self.expires_at > timezone.now()


class SupportAccessGrant(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="support_grants")
    staff_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_grants")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approved_support_grants")
    reason = models.TextField()
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_active(self):
        return not self.revoked_at and self.expires_at > timezone.now()
