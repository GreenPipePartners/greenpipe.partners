from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Invitation, Membership, Organization


class InvitationTests(TestCase):
    def test_login_links_to_password_reset(self):
        response = self.client.get(reverse("organizations:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{reverse("organizations:password_reset")}"')
        self.assertContains(response, "Forgot your password?")
        self.assertNotContains(response, "Flux: the Green Pipe controls workbench")

    def test_valid_invitation_creates_member_and_cannot_be_reused(self):
        inviter = get_user_model().objects.create_user("owner", password="password")
        organization = Organization.objects.create(name="Alpha", slug="alpha")
        invitation, token = Invitation.issue(
            organization=organization,
            email="new@example.com",
            role=Membership.Role.MAINTAINER,
            invited_by=inviter,
        )
        url = reverse("organizations:accept_invitation", args=[token])
        response = self.client.post(url, {
            "first_name": "New",
            "last_name": "User",
            "password1": "A-Strong-Test-Password-937!",
            "password2": "A-Strong-Test-Password-937!",
        })
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email="new@example.com")
        self.assertTrue(Membership.objects.filter(organization=organization, user=user, role=Membership.Role.MAINTAINER).exists())
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.accepted_at)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_existing_user_must_sign_in_then_can_accept(self):
        inviter = get_user_model().objects.create_user("owner", password="password")
        existing = get_user_model().objects.create_user("existing", email="existing@example.com", password="password")
        organization = Organization.objects.create(name="Alpha", slug="alpha")
        _, token = Invitation.issue(
            organization=organization,
            email=existing.email,
            role=Membership.Role.VIEWER,
            invited_by=inviter,
        )
        url = reverse("organizations:accept_invitation", args=[token])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(existing)
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertTrue(Membership.objects.filter(organization=organization, user=existing).exists())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_flow_has_namespaced_success_route(self):
        get_user_model().objects.create_user("customer", email="customer@example.com", password="password")
        response = self.client.post(reverse("organizations:password_reset"), {"email": "customer@example.com"})
        self.assertRedirects(response, reverse("organizations:password_reset_done"))
