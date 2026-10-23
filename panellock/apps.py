from django.apps import AppConfig


class PanelLockConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "panellock"
    verbose_name = "PanelLock"

    def ready(self):
        import certifi
        import stripe

        # Stripe ships its own CA bundle; use our explicitly patched dependency.
        stripe.ca_bundle_path = certifi.where()
