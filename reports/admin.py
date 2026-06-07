from django.contrib import admin

from .models import AlternativeInvestmentItem, CRMActionHistory, CRMActionItem, ClientReport


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


@admin.register(CRMActionItem)
class CRMActionItemAdmin(admin.ModelAdmin):
    list_display = ("client_name", "crm_owner", "status", "due_date", "updated_at")
    list_filter = ("status", "crm_owner")
    search_fields = ("client_name", "crm_owner", "action_item", "progress_update")
    ordering = ("client_name", "-updated_at")


@admin.register(CRMActionHistory)
class CRMActionHistoryAdmin(admin.ModelAdmin):
    list_display = ("client_name", "action_type", "actor_role", "status", "created_at")
    list_filter = ("action_type", "actor_role", "status")
    search_fields = ("client_name", "crm_owner", "action_item_text", "progress_update")
    ordering = ("-created_at",)


@admin.register(AlternativeInvestmentItem)
class AlternativeInvestmentItemAdmin(admin.ModelAdmin):
    list_display = (
        "investment_name",
        "client_name",
        "owner",
        "status",
        "last_update",
        "next_review_date",
        "updated_at",
    )
    list_filter = ("status", "owner", "category")
    search_fields = ("investment_name", "client_name", "category", "owner", "summary_update", "detailed_review")
    ordering = ("investment_name",)
