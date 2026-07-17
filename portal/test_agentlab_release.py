from django.test import SimpleTestCase
from django.urls import reverse


class AgentLabReleaseTests(SimpleTestCase):
    def test_agentlabs_page_links_public_vm(self):
        response = self.client.get(reverse("portal:agentlabs"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public VM release")
        self.assertContains(response, "GPP_VM-2026.07.15.qcow2")
        self.assertContains(
            response,
            "https://drive.google.com/file/d/17Uukhn7_MHFWiStWfjuujK2U-wU9hA0d/view?usp=drive_link",
        )
        self.assertContains(response, 'target="_blank"')
        self.assertContains(response, 'rel="noopener noreferrer"')
        self.assertContains(
            response,
            "db92866e2994a80bab201d3aeb3b7d0054dbb4b27fbafc52353c3e941e355420",
        )
        self.assertContains(response, "FluxLab-ChangeMe1")
        self.assertContains(response, "Docker Engine 29.1.3")
        self.assertContains(response, "Ignition</dt><dd>Not included")
        self.assertNotContains(response, "Ignition Gateway 8.3.4")
