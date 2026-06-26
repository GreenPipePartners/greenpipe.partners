from django.contrib import admin
from django.utils.html import format_html

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        "customer",
        "customer_name",
        "report_type",
        "title",
        "start_date",
        "end_date",
        "gist_id",
        "updated_at",
    ]
    list_filter = ["report_type", "customer"]
    readonly_fields = ["gist_id", "created_at", "updated_at"]
    search_fields = ["customer", "customer_name", "title", "gist_id", "gist_url"]

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.pk:
            readonly_fields.insert(1, "destination_url")
        return readonly_fields

    @admin.display(description="Destination URL")
    def destination_url(self, obj):
        url = obj.get_absolute_url()
        return format_html('<a href="{}">{}</a>', url, url)
