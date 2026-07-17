import base64
import hashlib
import json
import time
import uuid
from datetime import date, timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from organizations.models import Membership, Organization

from .models import (
    CatalogOffer,
    Device,
    DeviceCredential,
    EnrollmentToken,
    EstimateRequest,
    Panel,
    PanelAllowance,
    Project,
    ProvisioningPlan,
    UpdateRelease,
    UpdateRequest,
)
from .forms import ManagedUpdateForm
from .storage import create_upload
from .workflow import approve_plan, operations_digest


class PanelLockSelectorTests(TestCase):
    def builder_payload(self):
        return {
            "contact": {
                "company": "Example Plant",
                "name": "Ada Controls",
                "email": "ada@example.com",
                "project": "Line 1 modernization",
            },
            "configurations": [{
                "source_code": "factorytalk",
                "pc_code": "pc-small",
                "screen_code": "panel-small",
                "license_code": "license-edge-panel",
                "protect": True,
            }],
            "spares": [],
            "source_authorized": True,
            "agentlab_acknowledged": True,
        }

    def test_page_exposes_repeatable_conversion_quote_builder(self):
        response = self.client.get(reverse("panellock:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-panellock-builder")
        self.assertContains(response, f'data-proposal-endpoint="{reverse("panellock:builder_proposal")}"')
        self.assertContains(response, 'data-conversion-action="increment"')
        self.assertContains(response, 'data-conversion-action="decrement"')
        self.assertContains(response, 'class="ailab-required-card panellock-selector-shell"')
        self.assertContains(response, 'class="ailab-package-card panellock-config-card"', count=2)
        self.assertContains(response, 'class="ailab-summary-card"')
        self.assertContains(response, "Source platform type", count=2)
        self.assertContains(response, "PC type", count=2)
        self.assertContains(response, "Screen type", count=2)
        self.assertContains(response, "data-ignition-license", count=2)
        self.assertContains(
            response,
            'value="license-existing" data-label="Purchase Ignition Separately" data-price="0" selected',
            count=2,
        )
        self.assertContains(
            response,
            'value="license-edge-panel" data-label="Ignition Edge Panel" data-price="195000"',
            count=2,
        )
        self.assertContains(response, "Ignition Edge Panel - $1,950 USD", count=2)
        self.assertNotContains(response, "data-edge-license-detail")
        self.assertNotContains(response, "For visualization of data &amp; control of processes at the network&#x27;s edge.")
        self.assertNotContains(response, "Store tag history data for up to 35 days if connection is lost")
        self.assertContains(response, "Optional preconfigured spare PCs", count=1)
        self.assertContains(response, 'class="panellock-spare-option"', count=3)
        self.assertContains(response, 'data-spare-pc data-code="pc-small" data-label="Small PC - OnLogic CL260" data-price="128900"', count=1)
        self.assertContains(response, 'data-spare-pc data-code="pc-medium" data-label="Medium PC - OnLogic HX401" data-price="257200"', count=1)
        self.assertContains(response, 'data-spare-pc data-code="pc-large" data-label="Large PC - OnLogic HX401" data-price="456600"', count=1)
        self.assertContains(response, '<span class="panellock-spare-index">01</span>', count=1)
        self.assertContains(response, '<span class="panellock-spare-index">02</span>', count=1)
        self.assertContains(response, '<span class="panellock-spare-index">03</span>', count=1)
        self.assertContains(response, "Proposal total")
        self.assertContains(response, "Prompt the spare-PC build in OpenCode.")
        self.assertContains(response, "I have connected a spare PC to build it out as the new Fluxolot PC. Please build this and update it for me.")
        self.assertContains(response, "I'm on it. I'll use the connected AgentLab to inventory the spare")
        self.assertContains(response, "The spare Fluxolot PC build is complete.")
        self.assertContains(response, "data-prompt-story", count=1)
        self.assertContains(response, "data-story-panel", count=6)
        self.assertContains(response, "data-story-trigger", count=6)
        self.assertContains(response, "data-story-caption", count=6)
        self.assertContains(response, "data-story-playback", count=1)
        self.assertContains(response, "/static/portal/opencode-wordmark-dark.svg", count=1)
        self.assertContains(response, 'class="oc-landing__logo"', count=1)
        self.assertContains(response, "Generate Budgetary Proposal")
        self.assertContains(response, "View Saved Proposal")
        self.assertContains(response, "Budgetary proposal details")
        self.assertContains(response, "Green Pipe Partners expects to honor standard configurations as priced")
        self.assertContains(response, "Server-priced budgetary proposals remain valid for 30 days")
        self.assertContains(response, "PanelLock Protect")
        self.assertContains(response, "data-panel-protect", count=2)
        self.assertContains(response, "data-source-authorized", count=1)
        self.assertContains(response, "I confirm that I own or am authorized to use and provide the source projects", count=1)
        self.assertContains(response, "data-agentlab-acknowledged disabled", count=1)
        self.assertContains(response, "source-available AgentLab infrastructure that must be configured and maintained by qualified personnel", count=1)
        self.assertContains(response, "data-generate-proposal disabled")
        self.assertContains(response, 'data-request-final-approval aria-disabled="true"')
        self.assertContains(response, 'data-price="85000"', count=2)
        self.assertContains(response, "Ignition")
        self.assertContains(response, "Rockwell FactoryTalk View ME/SE")
        self.assertContains(response, '<optgroup label="Inductive Automation">', count=2)
        self.assertContains(response, '<optgroup label="Rockwell Automation">', count=2)
        self.assertContains(response, '<optgroup label="Siemens">', count=2)
        self.assertContains(response, 'value="ignition" data-label="Ignition" data-price="80000" selected', count=2)
        self.assertContains(response, "Pre-existing panel - $0", count=2)
        self.assertContains(response, 'data-price="80000"', count=2)
        self.assertContains(response, 'data-price="300000"')
        self.assertContains(response, "Customer portal")
        self.assertContains(response, "Panel and PC specifications")
        self.assertContains(response, 'class="panellock-spec-card"', count=8)
        self.assertContains(response, "Intel i7-1270PE")
        self.assertContains(response, "23.8 inch")
        self.assertContains(response, "Customer supplied")
        self.assertNotContains(response, "$3,000 / panel")
        self.assertNotContains(response, "$500 / year / panel")
        self.assertNotContains(response, "Quarterly update reviews")

    def test_protect_page_explains_managed_service_boundary(self):
        response = self.client.get(reverse("panellock:protect"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="hero solution-hero"')
        self.assertContains(response, "Keep every panel current, recoverable, and controlled")
        self.assertContains(response, "Protected backups")
        self.assertContains(response, "Two scheduled update reviews")
        self.assertContains(response, "Critical response")
        self.assertContains(response, "The same AgentLab, carried into panel operations")
        self.assertContains(response, "Source-available foundation")
        self.assertContains(response, "CISA-aligned practices")
        self.assertContains(response, "$850")
        self.assertContains(response, "per panel / year")
        self.assertContains(response, "does not guarantee uninterrupted operation")

    def test_proposal_uses_server_prices_and_preserves_vendor_link(self):
        response = self.client.post(
            reverse("panellock:builder_proposal"),
            data=json.dumps(self.builder_payload()),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        estimate = EstimateRequest.objects.get()
        self.assertEqual(estimate.one_time_total_cents, 741500)
        self.assertEqual(estimate.annual_total_cents, 85000)
        hardware = estimate.lines.get(code="pc-small")
        self.assertEqual(hardware.source_cost_cents, 99100)
        self.assertEqual(hardware.unit_amount_cents, 128900)
        self.assertIn("7fad3404-53f5-4262-9443-c3eefc41cb76", hardware.external_url)

        proposal = self.client.get(response.json()["proposal_url"])
        self.assertContains(proposal, "Budgetary pricing")
        self.assertContains(proposal, "$7,415")
        self.assertContains(proposal, "$850")
        self.assertContains(proposal, "valid through")

    def test_browser_prices_are_not_accepted(self):
        payload = self.builder_payload() | {"one_time_total_cents": 1, "amount_cents": 1}
        self.client.post(
            reverse("panellock:builder_proposal"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(EstimateRequest.objects.get().one_time_total_cents, 741500)

    def test_visible_builder_creates_authoritative_mixed_configuration_proposal(self):
        payload = {
            "contact": {
                "company": "Green Pipe Customer",
                "name": "Ada Controls",
                "email": "ada@example.com",
                "project": "Fluxolot modernization",
            },
            "configurations": [
                {
                    "source_code": "ignition",
                    "pc_code": "pc-small",
                    "screen_code": "panel-small",
                    "license_code": "license-edge-panel",
                    "protect": True,
                    "price": 1,
                },
                {
                    "source_code": "factorytalk",
                    "pc_code": "pc-medium",
                    "screen_code": "panel-medium",
                    "license_code": "license-existing",
                    "protect": False,
                    "price": 1,
                },
            ],
            "spares": [{"pc_code": "pc-large", "quantity": 2, "price": 1}],
            "source_authorized": True,
            "agentlab_acknowledged": True,
            "one_time_total_cents": 1,
        }

        response = self.client.post(
            reverse("panellock:builder_proposal"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        estimate = EstimateRequest.objects.get()
        self.assertEqual(data["reference"], estimate.reference)
        self.assertTrue(data["reference"].startswith("PL-"))
        self.assertEqual(estimate.one_time_total_cents, 2120300)
        self.assertEqual(estimate.annual_total_cents, 85000)
        self.assertEqual(data["one_time_total_cents"], 2120300)
        self.assertEqual(data["configuration"]["project"], "Fluxolot modernization")
        self.assertEqual(len(data["configuration"]["configurations"]), 2)
        self.assertEqual(data["configuration"]["spares"][0]["quantity"], 2)
        self.assertEqual(estimate.lines.filter(code="pc-large").get().quantity, 2)
        self.assertIn(str(estimate.id), data["proposal_url"])
        proposal = self.client.get(data["proposal_url"])
        self.assertContains(proposal, "$21,203")
        self.assertContains(proposal, "Fluxolot modernization")
        self.assertContains(proposal, "Green Pipe Partners expects to honor standard configurations")

    def test_builder_proposal_requires_protect_agentlab_acknowledgement(self):
        payload = {
            "contact": {
                "company": "Example Plant",
                "name": "Ada Controls",
                "email": "ada@example.com",
                "project": "Line 1",
            },
            "configurations": [{
                "source_code": "ignition",
                "pc_code": "pc-small",
                "screen_code": "panel-small",
                "license_code": "license-existing",
                "protect": True,
            }],
            "spares": [],
            "source_authorized": True,
            "agentlab_acknowledged": False,
        }

        response = self.client.post(
            reverse("panellock:builder_proposal"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Acknowledge the AgentLab requirement", status_code=400)
        self.assertFalse(EstimateRequest.objects.exists())

    def test_hardware_markup_rounds_up_to_the_next_dollar(self):
        offer = CatalogOffer.objects.create(
            code="rounding-test",
            category=CatalogOffer.Category.PC,
            name="Rounding test",
            cost_cents=101,
            markup_percent="15.00",
        )

        self.assertEqual(offer.amount_cents, 200)
        self.assertEqual(offer.display_price, "$2")

    def test_pc_catalog_uses_thirty_percent_markup(self):
        expected_prices = {
            "pc-small": 128900,
            "pc-medium": 257200,
            "pc-large": 456600,
        }
        for offer in CatalogOffer.objects.filter(code__in=expected_prices):
            self.assertEqual(offer.markup_percent, 30)
            self.assertEqual(offer.amount_cents, expected_prices[offer.code])
        self.assertEqual(CatalogOffer.objects.get(code="panel-small").markup_percent, 15)

    def test_index_accepts_only_the_visible_server_priced_workflow(self):
        response = self.client.post(reverse("panellock:index"), self.builder_payload())
        self.assertEqual(response.status_code, 405)
        self.assertFalse(EstimateRequest.objects.exists())

    def test_builder_rejects_non_panel_license_options(self):
        payload = self.builder_payload()
        payload["configurations"][0]["license_code"] = "license-vision"
        response = self.client.post(
            reverse("panellock:builder_proposal"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(EstimateRequest.objects.exists())

    def test_proposal_requires_expiring_signed_capability(self):
        self.client.post(
            reverse("panellock:builder_proposal"),
            data=json.dumps(self.builder_payload()),
            content_type="application/json",
        )
        estimate = EstimateRequest.objects.get()
        response = self.client.get(f"/panellock/proposal/{estimate.id}/invalid/")
        self.assertEqual(response.status_code, 404)


class TenantAndWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("maintainer", password="password")
        self.organization = Organization.objects.create(name="Alpha", slug="alpha")
        self.other = Organization.objects.create(name="Beta", slug="beta")
        Membership.objects.create(organization=self.organization, user=self.user, role=Membership.Role.MAINTAINER)
        self.panel = Panel.objects.create(organization=self.organization, name="Line 1")

    def test_portal_rejects_cross_tenant_access(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("panellock:organization_portal", args=[self.other.slug]))
        self.assertEqual(response.status_code, 403)

    def test_portal_renders_panel_inventory_and_project_actions(self):
        project = Project.objects.create(
            organization=self.organization,
            name="Fluxolot Tank Monitoring",
            source_platform="Ignition",
        )
        self.panel.project = project
        self.panel.name = "Tank Monitoring Panel"
        self.panel.ignition_version = "8.3.6"
        self.panel.ubuntu_version = "24.04.3 LTS"
        self.panel.scheduled_update_on = date(2020, 5, 5)
        self.panel.last_updated_on = date(2019, 11, 12)
        self.panel.release_attention = Panel.ReleaseAttention.DUE
        self.panel.certifications = ["PanelLock Baseline", "Backup Verified"]
        self.panel.save()
        PanelAllowance.objects.create(
            panel=self.panel,
            allowance_type=PanelAllowance.AllowanceType.COMMUNICATION,
            name="PLC communications path",
            details="Approved EtherNet/IP path on TCP 44818.",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("panellock:organization_portal", args=[self.organization.slug]))

        self.assertEqual(response.status_code, 200)
        for heading in (
            "Panel Project",
            "Ignition Version",
            "Ubuntu Version",
            "Scheduled Update date",
            "Last Updated",
            "Update Status",
            "Special Exceptions",
            "Certifications",
            "Gateway Upload",
        ):
            self.assertContains(response, heading)
        self.assertContains(response, "Fluxolot Tank Monitoring")
        self.assertContains(response, "Update due")
        self.assertContains(response, "8.3.6")
        self.assertContains(response, "24.04.3 LTS")
        self.assertContains(response, "May 5, 2020")
        self.assertContains(response, "Due")
        self.assertContains(response, "1 allowance")
        self.assertContains(response, "PanelLock Baseline")
        self.assertContains(
            response,
            reverse("panellock:gateway_upload", args=[self.organization.slug, project.id]),
        )
        self.assertContains(
            response,
            reverse("panellock:panel_connection", args=[self.organization.slug, self.panel.id]),
        )
        for removed_section in (
            "<h2>Update notices</h2>",
            "<h2>Backups</h2>",
            "<h2>Managed update requests</h2>",
            "No update notices.",
            "No backups uploaded.",
            "No update requests.",
        ):
            self.assertNotContains(response, removed_section)

    def test_allowance_register_and_gateway_upload_are_tenant_scoped(self):
        project = Project.objects.create(organization=self.organization, name="Tank Monitoring")
        self.panel.project = project
        self.panel.save(update_fields=["project", "updated_at"])
        second_project = Project.objects.create(organization=self.organization, name="Food Press Monitoring")
        second_panel = Panel.objects.create(
            organization=self.organization,
            project=second_project,
            name="Food Press Monitoring Panel",
        )
        other_project = Project.objects.create(organization=self.other, name="Other Customer Project")
        other_panel = Panel.objects.create(
            organization=self.other,
            project=other_project,
            name="Other Customer Panel",
        )
        PanelAllowance.objects.create(
            panel=self.panel,
            allowance_type=PanelAllowance.AllowanceType.APPLICATION,
            name="Ignition application permissions",
            details="Approved tag and alarm journal permissions.",
        )
        self.client.force_login(self.user)

        allowances = self.client.get(
            reverse("panellock:panel_allowances", args=[self.organization.slug, self.panel.id])
        )
        upload = self.client.get(
            reverse("panellock:gateway_upload", args=[self.organization.slug, project.id])
        )

        self.assertContains(allowances, "Ignition application permissions")
        self.assertContains(allowances, "Approved tag and alarm journal permissions")
        self.assertContains(upload, "Gateway Upload")
        self.assertContains(upload, "data-gateway-upload-form")
        self.assertContains(upload, "Tank Monitoring / Line 1")
        self.assertContains(upload, f'value="{second_panel.id}"')
        self.assertContains(upload, "Food Press Monitoring / Food Press Monitoring Panel")
        self.assertNotContains(upload, str(other_panel.id))
        self.assertNotContains(upload, "Other Customer Panel")
        self.assertEqual(
            self.client.get(
                reverse("panellock:panel_allowances", args=[self.other.slug, self.panel.id])
            ).status_code,
            403,
        )

    def test_due_panel_connection_issues_panel_bound_one_use_command(self):
        project = Project.objects.create(organization=self.organization, name="Tank Monitoring")
        self.panel.project = project
        self.panel.release_attention = Panel.ReleaseAttention.DUE
        self.panel.save(update_fields=["project", "release_attention", "updated_at"])
        self.client.force_login(self.user)
        url = reverse("panellock:panel_connection", args=[self.organization.slug, self.panel.id])

        page = self.client.get(url)

        self.assertContains(page, "Connect an AgentLab to Line 1")
        self.assertContains(page, "Prepare the independent uplink")
        self.assertContains(page, "Do not bridge, route, or NAT")
        self.assertContains(page, "sudo panellock-agent connect")
        self.assertContains(page, "&lt;one-use-token&gt;", html=False)
        self.assertEqual(EnrollmentToken.objects.count(), 0)

        command = self.client.post(url)

        enrollment = EnrollmentToken.objects.get()
        self.assertEqual(enrollment.organization, self.organization)
        self.assertEqual(enrollment.panel, self.panel)
        self.assertEqual(enrollment.intended_name, "AgentLab for Line 1")
        self.assertContains(command, "Run on the AgentLab")
        self.assertContains(command, "sudo panellock-agent connect")
        self.assertContains(command, "--portal http://testserver")
        self.assertNotContains(command, "&lt;one-use-token&gt;", html=False)
        self.assertEqual(
            self.client.get(
                reverse("panellock:panel_connection", args=[self.other.slug, self.panel.id])
            ).status_code,
            403,
        )

    def test_models_reject_cross_tenant_relationships(self):
        other_project = Project.objects.create(organization=self.other, name="Other project")
        with self.assertRaises(ValidationError):
            Panel.objects.create(organization=self.organization, project=other_project, name="Invalid")

    def test_plan_rejects_arbitrary_commands(self):
        release = UpdateRelease.objects.create(name="Ignition update", version="8.3.1", release_notes="Test")
        update = UpdateRequest.objects.create(
            organization=self.organization,
            panel=self.panel,
            release=release,
            requested_by=self.user,
        )
        device = Device.objects.create(organization=self.organization, name="Panel PC")
        plan = ProvisioningPlan(
            organization=self.organization,
            update_request=update,
            device=device,
            operations=[{"type": "install_signed_package", "shell": "rm -rf /"}],
            operations_sha256="bad",
        )
        with self.assertRaises(ValidationError):
            plan.full_clean()

    def test_approved_plan_is_immutable_and_queues_job(self):
        release = UpdateRelease.objects.create(name="Ignition update", version="8.3.1", release_notes="Test")
        update = UpdateRequest.objects.create(organization=self.organization, panel=self.panel, release=release, requested_by=self.user)
        device = Device.objects.create(organization=self.organization, name="Panel PC")
        operations = [{"type": "verify_prerequisites"}, {"type": "run_health_check", "profile": "ignition-panel"}]
        plan = ProvisioningPlan.objects.create(
            organization=self.organization,
            update_request=update,
            device=device,
            operations=operations,
            operations_sha256=operations_digest(operations),
        )
        job = approve_plan(plan, self.user)
        self.assertEqual(job.status, "queued")
        self.assertEqual(job.plan.approvals.get().operations_sha256, plan.operations_sha256)

    def test_replacement_plan_targets_selected_spare_and_matching_backup(self):
        from .models import BackupAsset, DeviceAssignment

        Membership.objects.filter(user=self.user).update(role=Membership.Role.OWNER)
        active = Device.objects.create(organization=self.organization, name="Active", status=Device.Status.ACTIVE)
        DeviceAssignment.objects.create(device=active, panel=self.panel)
        spare = Device.objects.create(organization=self.organization, name="Spare", status=Device.Status.SPARE)
        backup = BackupAsset.objects.create(
            organization=self.organization,
            panel=self.panel,
            uploaded_by=self.user,
            original_filename="panel.gwbk",
            object_key="clean/panel.gwbk",
            size_bytes=100,
            sha256="a" * 64,
            scan_status=BackupAsset.ScanStatus.CLEAN,
            retention_until=timezone.localdate() + timedelta(days=90),
        )
        release = UpdateRelease.objects.create(
            name="Ignition update",
            version="8.3.1",
            release_notes="Test",
            artifact_url="https://downloads.example.com/ignition.zip",
            artifact_sha256="b" * 64,
            published_at=timezone.now(),
        )
        self.client.force_login(self.user)
        response = self.client.post(reverse("panellock:managed_update", args=[self.organization.slug]), {
            "panel": self.panel.id,
            "release": release.id,
            "backup": backup.id,
            "maintenance_window": "2026-08-01T12:00",
            "request_text": "Prepare the replacement",
            "replacement": "on",
            "replacement_device": spare.id,
            "downtime_acknowledged": "on",
        })
        self.assertEqual(response.status_code, 302)
        plan = ProvisioningPlan.objects.get()
        self.assertEqual(plan.device, spare)
        self.assertEqual(plan.operations[1], {"type": "restore_approved_backup", "backup_id": str(backup.id)})

    def test_update_form_rejects_another_panels_backup(self):
        from .models import BackupAsset

        other_panel = Panel.objects.create(organization=self.organization, name="Line 2")
        backup = BackupAsset.objects.create(
            organization=self.organization,
            panel=other_panel,
            uploaded_by=self.user,
            original_filename="other.gwbk",
            object_key="clean/other.gwbk",
            size_bytes=100,
            sha256="a" * 64,
            scan_status=BackupAsset.ScanStatus.CLEAN,
            retention_until=timezone.localdate() + timedelta(days=90),
        )
        release = UpdateRelease.objects.create(
            name="Update",
            version="8.3.1",
            release_notes="Test",
            artifact_url="https://downloads.example.com/update.zip",
            artifact_sha256="b" * 64,
            published_at=timezone.now(),
        )
        form = ManagedUpdateForm({
            "panel": self.panel.id,
            "release": release.id,
            "backup": backup.id,
            "maintenance_window": "2026-08-01T12:00",
            "request_text": "Update",
            "downtime_acknowledged": "on",
        }, organization=self.organization)
        self.assertFalse(form.is_valid())
        self.assertIn("backup", form.errors)

    def test_restore_plan_is_bound_to_clean_request_backup(self):
        from .models import BackupAsset

        device = Device.objects.create(organization=self.organization, name="Spare", status=Device.Status.RESERVED)
        backup = BackupAsset.objects.create(
            organization=self.organization,
            panel=self.panel,
            uploaded_by=self.user,
            original_filename="panel.gwbk",
            object_key="clean/bound.gwbk",
            size_bytes=100,
            sha256="a" * 64,
            scan_status=BackupAsset.ScanStatus.CLEAN,
            retention_until=timezone.localdate() + timedelta(days=90),
        )
        release = UpdateRelease.objects.create(name="Update", version="8.3.1", release_notes="Test")
        update = UpdateRequest.objects.create(
            organization=self.organization,
            panel=self.panel,
            release=release,
            backup=backup,
            requested_by=self.user,
        )
        operations = [{"type": "restore_approved_backup", "backup_id": str(uuid.uuid4())}]
        with self.assertRaises(ValidationError):
            ProvisioningPlan.objects.create(
                organization=self.organization,
                update_request=update,
                device=device,
                operations=operations,
                operations_sha256=operations_digest(operations),
            )

    def test_backup_is_revalidated_at_approval(self):
        from .models import BackupAsset

        device = Device.objects.create(organization=self.organization, name="Spare", status=Device.Status.RESERVED)
        backup = BackupAsset.objects.create(
            organization=self.organization,
            panel=self.panel,
            uploaded_by=self.user,
            original_filename="panel.gwbk",
            object_key="clean/revalidate.gwbk",
            size_bytes=100,
            sha256="a" * 64,
            scan_status=BackupAsset.ScanStatus.CLEAN,
            retention_until=timezone.localdate() + timedelta(days=90),
        )
        release = UpdateRelease.objects.create(name="Update", version="8.3.1", release_notes="Test")
        update = UpdateRequest.objects.create(organization=self.organization, panel=self.panel, release=release, backup=backup, requested_by=self.user)
        operations = [{"type": "restore_approved_backup", "backup_id": str(backup.id)}]
        plan = ProvisioningPlan.objects.create(
            organization=self.organization,
            update_request=update,
            device=device,
            operations=operations,
            operations_sha256=operations_digest(operations),
        )
        backup.scan_status = BackupAsset.ScanStatus.QUARANTINED
        backup.save(update_fields=["scan_status", "updated_at"])
        with self.assertRaises(ValidationError):
            approve_plan(plan, self.user)

    def test_expired_plan_releases_reserved_spare(self):
        device = Device.objects.create(organization=self.organization, name="Spare", status=Device.Status.RESERVED)
        release = UpdateRelease.objects.create(name="Update", version="8.3.1", release_notes="Test")
        update = UpdateRequest.objects.create(organization=self.organization, panel=self.panel, release=release, requested_by=self.user)
        operations = [{"type": "verify_prerequisites"}]
        ProvisioningPlan.objects.create(
            organization=self.organization,
            update_request=update,
            device=device,
            operations=operations,
            operations_sha256=operations_digest(operations),
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        call_command("expire_panellock_plans")
        device.refresh_from_db()
        update.refresh_from_db()
        self.assertEqual(device.status, Device.Status.SPARE)
        self.assertEqual(update.status, UpdateRequest.Status.CANCELED)

    @override_settings(PANELLOCK_S3_LOCATIONS={"us-west": {"bucket": "west-bucket", "region": "us-west-2"}})
    def test_upload_uses_tenant_region_and_exact_size_checksum_policy(self):
        from unittest.mock import Mock, patch

        self.organization.data_region = Organization.Region.US_WEST
        self.organization.save()
        s3 = Mock()
        s3.generate_presigned_post.return_value = {"url": "https://west-bucket.example", "fields": {}}
        with patch("panellock.storage.boto3.client", return_value=s3) as client:
            result = create_upload(
                organization=self.organization,
                panel=self.panel,
                user=self.user,
                filename="panel.gwbk",
                size_bytes=100,
                sha256="a" * 64,
            )
        client.assert_called_once_with("s3", region_name="us-west-2")
        kwargs = s3.generate_presigned_post.call_args.kwargs
        self.assertEqual(kwargs["Bucket"], "west-bucket")
        self.assertIn(["content-length-range", 100, 100], kwargs["Conditions"])
        self.assertIn("upload", result)


class DeviceAuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("owner", password="password")
        self.organization = Organization.objects.create(name="Alpha", slug="alpha")
        self.panel = Panel.objects.create(organization=self.organization, name="Line 1")
        self.token_record, self.token = EnrollmentToken.issue(
            organization=self.organization,
            panel=self.panel,
            intended_name="Line 1 PC",
            as_spare=False,
            expires_at=timezone.now() + timedelta(hours=1),
            created_by=self.user,
        )
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def enroll(self):
        response = self.client.post(
            reverse("panellock:device_enroll"),
            data=json.dumps({
                "token": self.token,
                "public_key": base64.b64encode(self.public_key).decode(),
                "agent_version": "0.1.0",
                "inventory": {"mac_addresses": ["00:11:22:33:44:55"]},
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["device_id"]

    def signed_headers(self, device_id, path, body, nonce=None):
        timestamp = str(int(time.time()))
        nonce = nonce or str(uuid.uuid4())
        digest = hashlib.sha256(body).hexdigest()
        canonical = f"POST\n{path}\n{timestamp}\n{nonce}\n{digest}".encode()
        return {
            "HTTP_X_PANELLOCK_DEVICE": device_id,
            "HTTP_X_PANELLOCK_TIMESTAMP": timestamp,
            "HTTP_X_PANELLOCK_NONCE": nonce,
            "HTTP_X_PANELLOCK_SIGNATURE": base64.b64encode(self.private_key.sign(canonical)).decode(),
        }

    def test_mac_is_inventory_not_identity_and_replay_is_rejected(self):
        device_id = self.enroll()
        device = Device.objects.get(pk=device_id)
        self.assertEqual(device.inventory["mac_addresses"], ["00:11:22:33:44:55"])
        self.assertTrue(DeviceCredential.objects.filter(device=device).exists())

        path = reverse("panellock:device_heartbeat")
        body = json.dumps({"agent_version": "0.1.1", "inventory": {"mac_addresses": ["AA:BB:CC:DD:EE:FF"]}}).encode()
        nonce = str(uuid.uuid4())
        headers = self.signed_headers(device_id, path, body, nonce)
        first = self.client.post(path, data=body, content_type="application/json", **headers)
        second = self.client.post(path, data=body, content_type="application/json", **headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 401)

    def test_enrollment_token_is_single_use(self):
        self.enroll()
        response = self.client.post(
            reverse("panellock:device_enroll"),
            data=json.dumps({"token": self.token, "public_key": base64.b64encode(Ed25519PrivateKey.generate().public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)


class ReplacementCompletionTests(TestCase):
    def setUp(self):
        from .models import BackupAsset, DeviceAssignment

        self.user = get_user_model().objects.create_user("maintainer", password="password")
        self.organization = Organization.objects.create(name="Alpha", slug="alpha")
        self.panel = Panel.objects.create(organization=self.organization, name="Line 1")
        self.old_device = Device.objects.create(organization=self.organization, name="Old", status=Device.Status.ACTIVE)
        DeviceAssignment.objects.create(device=self.old_device, panel=self.panel)
        self.old_key = self.add_credential(self.old_device)
        self.spare = Device.objects.create(organization=self.organization, name="Spare", status=Device.Status.RESERVED)
        self.spare_key = self.add_credential(self.spare)
        backup = BackupAsset.objects.create(
            organization=self.organization,
            panel=self.panel,
            uploaded_by=self.user,
            original_filename="panel.gwbk",
            object_key="clean/replacement.gwbk",
            size_bytes=100,
            sha256="a" * 64,
            scan_status=BackupAsset.ScanStatus.CLEAN,
            retention_until=timezone.localdate() + timedelta(days=90),
        )
        release = UpdateRelease.objects.create(name="Update", version="8.3.1", release_notes="Test")
        update = UpdateRequest.objects.create(
            organization=self.organization,
            panel=self.panel,
            release=release,
            backup=backup,
            requested_by=self.user,
        )
        operations = [{"type": "restore_approved_backup", "backup_id": str(backup.id)}]
        plan = ProvisioningPlan.objects.create(
            organization=self.organization,
            update_request=update,
            device=self.spare,
            operations=operations,
            operations_sha256=operations_digest(operations),
        )
        self.job = approve_plan(plan, self.user)
        self.job.status = "claimed"
        self.job.save(update_fields=["status", "updated_at"])

    def add_credential(self, device):
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        DeviceCredential.objects.create(
            device=device,
            public_key=base64.b64encode(public_key).decode(),
            fingerprint=hashlib.sha256(public_key).hexdigest(),
        )
        return private_key

    def signed_headers(self, device, private_key, path, body):
        timestamp = str(int(time.time()))
        nonce = str(uuid.uuid4())
        digest = hashlib.sha256(body).hexdigest()
        canonical = f"POST\n{path}\n{timestamp}\n{nonce}\n{digest}".encode()
        return {
            "HTTP_X_PANELLOCK_DEVICE": str(device.id),
            "HTTP_X_PANELLOCK_TIMESTAMP": timestamp,
            "HTTP_X_PANELLOCK_NONCE": nonce,
            "HTTP_X_PANELLOCK_SIGNATURE": base64.b64encode(private_key.sign(canonical)).decode(),
        }

    def test_completion_atomically_reassigns_and_revokes_old_device(self):
        from .models import DeviceAssignment

        path = reverse("panellock:device_job_event", args=[self.job.id])
        started_body = json.dumps({"sequence": 0, "event_type": "started", "payload": {}}).encode()
        started = self.client.post(path, data=started_body, content_type="application/json", **self.signed_headers(self.spare, self.spare_key, path, started_body))
        self.assertEqual(started.status_code, 202)
        body = json.dumps({"sequence": 1, "event_type": "completed", "payload": {"health": "ok"}}).encode()
        response = self.client.post(path, data=body, content_type="application/json", **self.signed_headers(self.spare, self.spare_key, path, body))
        self.assertEqual(response.status_code, 202)
        self.old_device.refresh_from_db()
        self.spare.refresh_from_db()
        self.job.plan.update_request.refresh_from_db()
        self.assertEqual(self.old_device.status, Device.Status.RETIRED)
        self.assertIsNotNone(self.old_device.credential.revoked_at)
        self.assertEqual(self.spare.status, Device.Status.ACTIVE)
        self.assertEqual(DeviceAssignment.objects.get(panel=self.panel, ended_at__isnull=True).device, self.spare)
        self.assertEqual(self.job.plan.update_request.status, UpdateRequest.Status.COMPLETED)

        late_body = json.dumps({"sequence": 2, "event_type": "failed", "payload": {}}).encode()
        late = self.client.post(path, data=late_body, content_type="application/json", **self.signed_headers(self.spare, self.spare_key, path, late_body))
        self.assertEqual(late.status_code, 409)

        heartbeat = reverse("panellock:device_heartbeat")
        heartbeat_body = b"{}"
        retired_response = self.client.post(
            heartbeat,
            data=heartbeat_body,
            content_type="application/json",
            **self.signed_headers(self.old_device, self.old_key, heartbeat, heartbeat_body),
        )
        self.assertEqual(retired_response.status_code, 401)
