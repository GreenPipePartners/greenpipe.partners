from django.db import migrations


HARDWARE = {
    "pc-small": {
        "description": "Intel N250, 8 GB, 128 GB SSD, Ubuntu 24.04 and selected industrial accessories.",
        "specifications": {
            "Model": "OnLogic CL260",
            "Processor": "Intel N250",
            "Memory": "8 GB",
            "Storage": "128 GB SSD",
            "Operating system": "Ubuntu 24.04",
        },
    },
    "pc-medium": {
        "description": "Intel i3-1220PE, 8 GB, 128 GB SSD and Ubuntu 24.04.",
        "specifications": {
            "Model": "OnLogic HX401",
            "Processor": "Intel i3-1220PE",
            "Memory": "8 GB",
            "Storage": "128 GB SSD",
            "Operating system": "Ubuntu 24.04",
        },
    },
    "pc-large": {
        "description": "Intel i7-1270PE, 16 GB, 256 GB SSD and Ubuntu 24.04.",
        "specifications": {
            "Model": "OnLogic HX401",
            "Processor": "Intel i7-1270PE",
            "Memory": "16 GB",
            "Storage": "256 GB SSD",
            "Operating system": "Ubuntu 24.04",
        },
    },
    "panel-small": {
        "description": "OnLogic TN101R industrial panel display with a 12.1 inch resistive touchscreen.",
        "specifications": {
            "Model": "OnLogic TN101R",
            "Display size": "12.1 inch",
            "Touch technology": "Resistive",
        },
    },
    "panel-medium": {
        "description": "OnLogic TN101R industrial panel display with a 15.6 inch resistive touchscreen.",
        "specifications": {
            "Model": "OnLogic TN101R",
            "Display size": "15.6 inch",
            "Touch technology": "Resistive",
        },
    },
    "panel-large": {
        "description": "OnLogic TN101R industrial panel display with a 21.5 inch resistive touchscreen.",
        "specifications": {
            "Model": "OnLogic TN101R",
            "Display size": "21.5 inch",
            "Touch technology": "Resistive",
        },
    },
    "panel-xlarge": {
        "description": "OnLogic TN101R industrial panel display with a 23.8 inch resistive touchscreen.",
        "specifications": {
            "Model": "OnLogic TN101R",
            "Display size": "23.8 inch",
            "Touch technology": "Resistive",
        },
    },
    "panel-existing": {
        "description": "Customer supplies a compatible existing panel display.",
        "specifications": {
            "Hardware": "Customer supplied",
            "Compatibility": "Reviewed before quote acceptance",
            "Reuse scope": "Existing panel display",
        },
    },
}


def add_hardware_specifications(apps, schema_editor):
    catalog_offer = apps.get_model("panellock", "CatalogOffer")
    for code, values in HARDWARE.items():
        catalog_offer.objects.filter(code=code).update(**values)


class Migration(migrations.Migration):
    dependencies = [("panellock", "0008_add_preexisting_panel_offer")]

    operations = [migrations.RunPython(add_hardware_specifications, migrations.RunPython.noop)]
