from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone

from .catalog import SOURCE_PLATFORM_GROUPS
from .models import CatalogOffer, EstimateLine, EstimateRequest


def create_builder_estimate(payload):
    configurations = payload.get("configurations")
    spares = payload.get("spares", [])
    contact = payload.get("contact", {})
    if not isinstance(configurations, list) or not 1 <= len(configurations) <= 20:
        raise ValidationError("Select between one and twenty panel configurations.")
    if not isinstance(spares, list) or not isinstance(contact, dict):
        raise ValidationError("The proposal request is malformed.")
    if payload.get("source_authorized") is not True:
        raise ValidationError("Source authorization is required.")

    contact_name = str(contact.get("name", "")).strip()
    company = str(contact.get("company", "")).strip()
    email = str(contact.get("email", "")).strip()
    project_name = str(contact.get("project", "")).strip()
    if not contact_name or len(contact_name) > 120:
        raise ValidationError("Enter a valid proposal contact name.")
    if not company or len(company) > 160:
        raise ValidationError("Enter a valid company name.")
    if not project_name or len(project_name) > 160:
        raise ValidationError("Enter a project or site name.")
    validate_email(email)

    offers = {offer.code: offer for offer in CatalogOffer.objects.filter(is_active=True)}
    source_names = {
        code: name
        for _, platforms in SOURCE_PLATFORM_GROUPS
        for code, name in platforms
    }
    allowed_licenses = {"license-existing", "license-edge-panel"}
    normalized_configurations = []
    normalized_spares = []
    line_specs = []
    protect_selected = False

    for index, selection in enumerate(configurations, start=1):
        if not isinstance(selection, dict):
            raise ValidationError("A panel configuration is malformed.")
        source_code = str(selection.get("source_code", ""))
        pc = offers.get(str(selection.get("pc_code", "")))
        panel = offers.get(str(selection.get("screen_code", "")))
        license_offer = offers.get(str(selection.get("license_code", "")))
        if source_code not in source_names:
            raise ValidationError("Select a supported source platform.")
        if not pc or pc.category != CatalogOffer.Category.PC:
            raise ValidationError("Select a valid industrial PC.")
        if not panel or panel.category != CatalogOffer.Category.PANEL:
            raise ValidationError("Select a valid panel display.")
        if not license_offer or license_offer.code not in allowed_licenses:
            raise ValidationError("Select a valid per-panel Ignition license option.")

        conversion = offers["ignition-panel-upgrade" if source_code == "ignition" else "hmi-conversion"]
        protect = selection.get("protect") is True
        protect_offer = offers["managed-panel"] if protect else None
        one_time_total = sum(
            offer.amount_cents or 0
            for offer in (conversion, pc, panel, license_offer)
        )
        annual_total = protect_offer.amount_cents if protect_offer else 0
        normalized = {
            "source": {"code": source_code, "label": source_names[source_code], "price": conversion.amount_cents or 0},
            "pc": {"code": pc.code, "label": pc.name, "price": pc.amount_cents or 0},
            "screen": {"code": panel.code, "label": panel.name, "price": panel.amount_cents or 0},
            "license": {"code": license_offer.code, "label": license_offer.name, "price": license_offer.amount_cents or 0},
            "total": one_time_total,
            "annual": annual_total,
        }
        normalized_configurations.append(normalized)
        line_specs.extend([
            (conversion, 1, f"Panel {index:02d}: {conversion.name}"),
            (pc, 1, f"Panel {index:02d}: {pc.name}"),
            (panel, 1, f"Panel {index:02d}: {panel.name}"),
            (license_offer, 1, f"Panel {index:02d}: {license_offer.name}"),
        ])
        if protect_offer:
            protect_selected = True
            line_specs.append((protect_offer, 1, f"Panel {index:02d}: {protect_offer.name}"))

    if protect_selected and payload.get("agentlab_acknowledged") is not True:
        raise ValidationError("Acknowledge the AgentLab requirement for PanelLock Protect.")

    for selection in spares:
        if not isinstance(selection, dict):
            raise ValidationError("A spare-PC selection is malformed.")
        quantity = selection.get("quantity")
        pc = offers.get(str(selection.get("pc_code", "")))
        if not isinstance(quantity, int) or not 0 <= quantity <= 20:
            raise ValidationError("Spare-PC quantities must be between zero and twenty.")
        if not pc or pc.category != CatalogOffer.Category.PC:
            raise ValidationError("Select a valid spare PC.")
        if not quantity:
            continue
        normalized_spares.append({
            "code": pc.code,
            "label": pc.name,
            "price": pc.amount_cents or 0,
            "quantity": quantity,
            "total": (pc.amount_cents or 0) * quantity,
        })
        line_specs.append((pc, quantity, f"Preconfigured spare: {pc.name}"))

    source_labels = sorted({configuration["source"]["label"] for configuration in normalized_configurations})
    source_platform = source_labels[0] if len(source_labels) == 1 else "Mixed source platforms"
    project_type = (
        EstimateRequest.ProjectType.UPGRADE
        if all(configuration["source"]["code"] == "ignition" for configuration in normalized_configurations)
        else EstimateRequest.ProjectType.CONVERSION
    )
    normalized_payload = {
        "project": project_name,
        "configurations": normalized_configurations,
        "spares": normalized_spares,
        "source_authorized": True,
        "agentlab_acknowledged": payload.get("agentlab_acknowledged") is True,
    }

    with transaction.atomic():
        estimate = EstimateRequest.objects.create(
            project_type=project_type,
            source_platform=source_platform,
            panel_quantity=len(normalized_configurations),
            screen_count=len(normalized_configurations),
            contact_name=contact_name,
            company=company,
            email=email,
            follow_up_requested=False,
            configuration=normalized_payload,
            notes=f"Budgetary proposal for {project_name}",
            terms_accepted_at=timezone.now(),
        )
        lines = []
        one_time_total = 0
        annual_total = 0
        for offer, quantity, description in line_specs:
            amount = offer.amount_cents or 0
            lines.append(EstimateLine(
                estimate=estimate,
                offer=offer,
                code=offer.code,
                description=description,
                quantity=quantity,
                unit_amount_cents=amount,
                cadence=offer.cadence,
                source_cost_cents=offer.cost_cents,
                external_url=offer.external_url,
                price_checked_at=offer.price_checked_at,
            ))
            if offer.cadence == CatalogOffer.Cadence.ANNUAL:
                annual_total += amount * quantity
            else:
                one_time_total += amount * quantity
        EstimateLine.objects.bulk_create(lines)
        estimate.one_time_total_cents = one_time_total
        estimate.annual_total_cents = annual_total
        estimate.save(update_fields=["one_time_total_cents", "annual_total_cents", "updated_at"])
        return estimate
