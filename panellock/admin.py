from django.contrib import admin

from .models import (
    AuditEvent,
    BackupAsset,
    CatalogOffer,
    Device,
    EnrollmentToken,
    EstimateLine,
    EstimateRequest,
    FollowUpRequest,
    ManagedCoverage,
    Panel,
    PanelAllowance,
    Project,
    ProvisioningPlan,
    Site,
    UpdateJob,
    UpdateNotice,
    UpdateRelease,
    UpdateRequest,
)


class EstimateLineInline(admin.TabularInline):
    model = EstimateLine
    extra = 0
    readonly_fields = [field.name for field in EstimateLine._meta.fields if field.name != "id"]


@admin.register(CatalogOffer)
class CatalogOfferAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "display_price", "markup_percent", "price_checked_at", "is_active"]
    list_filter = ["category", "is_active", "cadence"]
    search_fields = ["code", "name"]


@admin.register(EstimateRequest)
class EstimateRequestAdmin(admin.ModelAdmin):
    list_display = ["reference", "company", "project_type", "panel_quantity", "status", "follow_up_requested", "created_at"]
    list_filter = ["project_type", "status", "follow_up_requested"]
    search_fields = ["company", "contact_name", "email"]
    readonly_fields = ["id", "created_at", "updated_at", "one_time_total_cents", "annual_total_cents"]
    inlines = [EstimateLineInline]


admin.site.register(FollowUpRequest)
admin.site.register(Site)
admin.site.register(Project)
admin.site.register(Panel)
admin.site.register(PanelAllowance)
admin.site.register(Device)
admin.site.register(EnrollmentToken)
admin.site.register(BackupAsset)
admin.site.register(ManagedCoverage)
admin.site.register(UpdateRelease)
admin.site.register(UpdateNotice)
admin.site.register(UpdateRequest)
admin.site.register(ProvisioningPlan)
admin.site.register(UpdateJob)
admin.site.register(AuditEvent)
