from django.test import SimpleTestCase, override_settings
from django.urls import reverse


class PicnicRedirectTests(SimpleTestCase):
    @override_settings(PICNIC_REDIRECT_URL="https://example.com/current-signup")
    def test_picnic_paths_redirect_to_configured_destination_without_caching(self):
        canonical_url = reverse("portal:picnic_redirect")
        self.assertEqual(canonical_url, "/picnic")

        for url in (canonical_url, "/picnic/"):
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response["Location"],
                    "https://example.com/current-signup",
                )
                self.assertEqual(response["Cache-Control"], "no-store, max-age=0")
                self.assertEqual(response["Pragma"], "no-cache")
                self.assertEqual(response["Referrer-Policy"], "no-referrer")
                self.assertEqual(response["X-Robots-Tag"], "noindex")
