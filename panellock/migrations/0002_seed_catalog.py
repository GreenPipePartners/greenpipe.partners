from datetime import date
from decimal import Decimal

from django.db import migrations


CHECKED = date(2026, 7, 16)

OFFERS = [
    {
        "code": "hmi-conversion",
        "category": "service",
        "name": "HMI project conversion to Ignition",
        "description": "Flat fee for one qualifying, extractable source HMI project/panel.",
        "amount_cents": 300000,
        "cadence": "once",
        "sort_order": 10,
    },
    {
        "code": "ignition-panel-upgrade",
        "category": "service",
        "name": "Existing Ignition panel upgrade",
        "description": "Upgrade one existing Ignition panel. Gateway work is custom-priced.",
        "amount_cents": 80000,
        "cadence": "once",
        "sort_order": 20,
    },
    {
        "code": "gateway-custom",
        "category": "service",
        "name": "Gateway or multi-panel engineering",
        "description": "Scope and price confirmed with Green Pipe Partners.",
        "amount_cents": None,
        "cadence": "custom",
        "sort_order": 30,
    },
    {
        "code": "managed-panel",
        "category": "subscription",
        "name": "PanelLock Protect",
        "description": "Semi-annual update reviews, protected backups, notifications, and out-of-cycle critical security patches or mitigations.",
        "amount_cents": 85000,
        "cadence": "annual",
        "sort_order": 10,
    },
    {
        "code": "pc-small",
        "category": "pc",
        "name": "Small PC - OnLogic CL260",
        "description": "Intel N250, 8 GB, 128 GB SSD, Ubuntu 24.04 and selected industrial accessories.",
        "cost_cents": 99100,
        "amount_cents": 114000,
        "markup_percent": Decimal("15.00"),
        "external_url": "https://www.onlogic.com/store/cl260?config=7fad3404-53f5-4262-9443-c3eefc41cb76",
        "price_checked_at": CHECKED,
        "specifications": {
            "Model": "OnLogic CL260",
            "Processor": "Intel N250",
            "Memory": "8 GB",
            "Storage": "128 GB SSD",
            "Operating system": "Ubuntu 24.04",
        },
        "sort_order": 10,
    },
    {
        "code": "pc-medium",
        "category": "pc",
        "name": "Medium PC - OnLogic HX401",
        "description": "Intel i3-1220PE, 8 GB, 128 GB SSD and Ubuntu 24.04.",
        "cost_cents": 197800,
        "amount_cents": 227500,
        "markup_percent": Decimal("15.00"),
        "external_url": "https://www.onlogic.com/store/hx401?config=61ba61e3-5282-47c5-9370-cc0df374ae73",
        "price_checked_at": CHECKED,
        "specifications": {
            "Model": "OnLogic HX401",
            "Processor": "Intel i3-1220PE",
            "Memory": "8 GB",
            "Storage": "128 GB SSD",
            "Operating system": "Ubuntu 24.04",
        },
        "sort_order": 20,
    },
    {
        "code": "pc-large",
        "category": "pc",
        "name": "Large PC - OnLogic HX401",
        "description": "Intel i7-1270PE, 16 GB, 256 GB SSD and Ubuntu 24.04.",
        "cost_cents": 351200,
        "amount_cents": 403900,
        "markup_percent": Decimal("15.00"),
        "external_url": "https://www.onlogic.com/store/hx401?config=e71aaf9c-7133-42d1-88a2-1bca0c973d11",
        "price_checked_at": CHECKED,
        "specifications": {
            "Model": "OnLogic HX401",
            "Processor": "Intel i7-1270PE",
            "Memory": "16 GB",
            "Storage": "256 GB SSD",
            "Operating system": "Ubuntu 24.04",
        },
        "sort_order": 30,
    },
    {
        "code": "panel-small",
        "category": "panel",
        "name": "Small resistive - 12.1 inch TN101R",
        "description": "OnLogic TN101R industrial panel display with a 12.1 inch resistive touchscreen.",
        "cost_cents": 102200,
        "amount_cents": 117600,
        "markup_percent": Decimal("15.00"),
        "external_url": "https://www.onlogic.com/store/tn101r?config=19d63771-90bf-4f1b-950d-01b778cd2aed",
        "price_checked_at": CHECKED,
        "specifications": {
            "Model": "OnLogic TN101R",
            "Display size": "12.1 inch",
            "Touch technology": "Resistive",
        },
        "sort_order": 10,
    },
    {
        "code": "panel-medium",
        "category": "panel",
        "name": "Medium resistive - 15.6 inch TN101R",
        "description": "OnLogic TN101R industrial panel display with a 15.6 inch resistive touchscreen.",
        "cost_cents": 111600,
        "amount_cents": 128400,
        "markup_percent": Decimal("15.00"),
        "external_url": "https://www.onlogic.com/store/tn101r?config=12408685-921c-471d-b7b5-4be794e7a816",
        "price_checked_at": CHECKED,
        "specifications": {
            "Model": "OnLogic TN101R",
            "Display size": "15.6 inch",
            "Touch technology": "Resistive",
        },
        "sort_order": 20,
    },
    {
        "code": "panel-large",
        "category": "panel",
        "name": "Large resistive - 21.5 inch TN101R",
        "description": "OnLogic TN101R industrial panel display with a 21.5 inch resistive touchscreen.",
        "cost_cents": 142000,
        "amount_cents": 163300,
        "markup_percent": Decimal("15.00"),
        "external_url": "https://www.onlogic.com/store/tn101r?config=5d3817e7-9815-4001-a31c-c08c81aa9f7f",
        "price_checked_at": CHECKED,
        "specifications": {
            "Model": "OnLogic TN101R",
            "Display size": "21.5 inch",
            "Touch technology": "Resistive",
        },
        "sort_order": 30,
    },
    {
        "code": "panel-xlarge",
        "category": "panel",
        "name": "X-large resistive - 23.8 inch TN101R",
        "description": "OnLogic TN101R industrial panel display with a 23.8 inch resistive touchscreen.",
        "cost_cents": 167200,
        "amount_cents": 192300,
        "markup_percent": Decimal("15.00"),
        "external_url": "https://www.onlogic.com/store/tn101r?config=ced30c6b-f077-46e5-8618-16a56c0a274a",
        "price_checked_at": CHECKED,
        "specifications": {
            "Model": "OnLogic TN101R",
            "Display size": "23.8 inch",
            "Touch technology": "Resistive",
        },
        "sort_order": 40,
    },
    {
        "code": "panel-existing",
        "category": "panel",
        "name": "Pre-existing panel",
        "description": "Customer supplies a compatible existing panel display.",
        "cost_cents": 0,
        "amount_cents": 0,
        "markup_percent": Decimal("0"),
        "specifications": {
            "Hardware": "Customer supplied",
            "Compatibility": "Reviewed before quote acceptance",
            "Reuse scope": "Existing panel display",
        },
        "sort_order": 50,
    },
    {
        "code": "license-existing",
        "category": "license",
        "name": "Use existing Ignition license",
        "description": "Customer supplies a compatible license.",
        "amount_cents": 0,
        "price_checked_at": CHECKED,
        "sort_order": 10,
    },
    {
        "code": "license-edge-panel",
        "category": "license",
        "name": "Ignition Edge Panel - manufacturer list price",
        "description": "Perpetual Edge Panel license with limited Vision or Perspective visualization.",
        "amount_cents": 195000,
        "external_url": "https://inductiveautomation.com/pricing/edge",
        "price_checked_at": CHECKED,
        "sort_order": 20,
    },
    {
        "code": "license-vision",
        "category": "license",
        "name": "Ignition Platform + Vision - manufacturer list price",
        "description": "$1,200 platform plus $8,330 Vision module; one perpetual gateway license.",
        "amount_cents": 953000,
        "external_url": "https://inductiveautomation.com/pricing/list",
        "price_checked_at": CHECKED,
        "sort_order": 30,
    },
    {
        "code": "license-perspective",
        "category": "license",
        "name": "Ignition Platform + Perspective - manufacturer list price",
        "description": "$1,200 platform plus $11,225 Perspective module; one perpetual gateway license.",
        "amount_cents": 1242500,
        "external_url": "https://inductiveautomation.com/pricing/list",
        "price_checked_at": CHECKED,
        "sort_order": 40,
    },
]


def seed_catalog(apps, schema_editor):
    CatalogOffer = apps.get_model("panellock", "CatalogOffer")
    for offer in OFFERS:
        code = offer["code"]
        defaults = {"cadence": "once", "markup_percent": Decimal("0"), **offer}
        defaults.pop("code")
        CatalogOffer.objects.update_or_create(code=code, defaults=defaults)


def remove_catalog(apps, schema_editor):
    CatalogOffer = apps.get_model("panellock", "CatalogOffer")
    CatalogOffer.objects.filter(code__in=[offer["code"] for offer in OFFERS]).delete()


class Migration(migrations.Migration):
    dependencies = [("panellock", "0001_initial")]
    operations = [migrations.RunPython(seed_catalog, remove_catalog)]
