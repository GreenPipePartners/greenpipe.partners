from django.contrib import admin

from .models import Invitation, Membership, Organization, SupportAccessGrant


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "data_region", "ai_processing_enabled", "created_at"]
    search_fields = ["name", "slug"]
    inlines = [MembershipInline]


admin.site.register(Invitation)
admin.site.register(SupportAccessGrant)
