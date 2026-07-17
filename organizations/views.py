import hashlib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import InvitationAcceptanceForm, InvitationForm
from .models import Invitation, Membership, Organization
from .services import require_membership


@login_required
def invite_member(request, organization_slug):
    organization = get_object_or_404(Organization, slug=organization_slug)
    require_membership(request.user, organization, Membership.Role.OWNER)
    form = InvitationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        invitation, token = Invitation.issue(
            organization=organization,
            email=form.cleaned_data["email"],
            role=form.cleaned_data["role"],
            invited_by=request.user,
        )
        url = request.build_absolute_uri(reverse("organizations:accept_invitation", args=[token]))
        send_mail(
            f"Invitation to {organization.name} on PanelLock",
            f"You have been invited to {organization.name}. Accept within 72 hours: {url}",
            settings.DEFAULT_FROM_EMAIL,
            [invitation.email],
        )
        messages.success(request, f"Invitation sent to {invitation.email}.")
        return redirect("panellock:organization_portal", organization_slug=organization.slug)
    return render(request, "organizations/invite.html", {"form": form, "organization": organization})


def accept_invitation(request, token):
    invitation = Invitation.objects.filter(token_hash=hashlib.sha256(token.encode()).hexdigest()).first()
    if not invitation or not invitation.is_active:
        raise Http404("Invitation is invalid or expired.")

    existing_user = get_user_model().objects.filter(email__iexact=invitation.email).first()
    if existing_user:
        if not request.user.is_authenticated or request.user != existing_user:
            messages.info(request, "Sign in to accept this invitation with your existing account.")
            return redirect(f"{reverse('organizations:login')}?next={request.path}")
        with transaction.atomic():
            locked = Invitation.objects.select_for_update().get(pk=invitation.pk)
            if not locked.is_active:
                raise Http404("Invitation is invalid or expired.")
            Membership.objects.get_or_create(
                organization=locked.organization,
                user=existing_user,
                defaults={"role": locked.role},
            )
            locked.accepted_at = timezone.now()
            locked.save(update_fields=["accepted_at"])
        messages.success(request, f"You now have access to {locked.organization.name}.")
        return redirect("panellock:organization_portal", organization_slug=locked.organization.slug)

    form = InvitationAcceptanceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            locked = Invitation.objects.select_for_update().get(pk=invitation.pk)
            if not locked.is_active:
                raise Http404("Invitation is invalid or expired.")
            user = form.save(commit=False)
            user.username = locked.email.lower()
            user.email = locked.email.lower()
            user.save()
            Membership.objects.create(organization=locked.organization, user=user, role=locked.role)
            locked.accepted_at = timezone.now()
            locked.save(update_fields=["accepted_at"])
        messages.success(request, "Account created. Sign in to open PanelLock.")
        return redirect("organizations:login")
    return render(request, "organizations/accept_invitation.html", {"form": form, "invitation": invitation})
