from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["customer", "customer_name", "start_date", "end_date", "gist_id", "updated_at"]
    list_filter = ["customer"]
    readonly_fields = ["gist_id", "created_at", "updated_at"]
    search_fields = ["customer", "customer_name", "gist_id", "gist_url"]
