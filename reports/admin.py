from django.contrib import admin

from .models import ClientReport


@admin.register(ClientReport)
class ClientReportAdmin(admin.ModelAdmin):
    list_display = (
        "client_name",
        "crm_name",
        "operations_assignee",
        "status_phase",
        "submitted_tick",
        "reviewed_tick",
        "sent_to_client_tick",
        "due_date",
    )
    list_filter = ("operations_assignee", "crm_name", "status_phase")
    search_fields = ("client_name", "crm_name", "operations_assignee")
    ordering = ("operations_assignee", "crm_name", "client_name")
    list_editable = ("status_phase",)
