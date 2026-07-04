from django.contrib import admin

from .models import AlternativeInvestmentItem, CRMActionHistory, CRMActionItem, ClientReport, Proposal, ProposalDocument, SharePointTrackerEntry


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


@admin.register(SharePointTrackerEntry)
class SharePointTrackerEntryAdmin(admin.ModelAdmin):
    list_display = (
        "client_name",
        "crm_name",
        "alternate_name",
        "word_submitted",
        "excel_submitted",
        "pdf_submitted",
        "status",
        "due_date",
    )
    list_filter = ("status", "word_submitted", "excel_submitted", "pdf_submitted")
    search_fields = ("client_name", "crm_name", "alternate_name")
    list_editable = ("word_submitted", "excel_submitted", "pdf_submitted", "status")


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


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ("proposal_name", "date", "status", "created_by", "updated_at")
    list_filter = ("status", "created_by")
    search_fields = ("proposal_name", "description")
    ordering = ("-date", "proposal_name")


@admin.register(ProposalDocument)
class ProposalDocumentAdmin(admin.ModelAdmin):
    list_display = ("proposal", "document_name", "file", "uploaded_at")
    search_fields = ("document_name", "proposal__proposal_name")


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
