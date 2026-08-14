from datetime import timedelta

from django.contrib import messages
from django.core.management import call_command
from django.core.paginator import Paginator
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import AlternativeInvestmentItemForm, DashboardSettingsForm, ProposalForm, ReportStatusForm, SharePointTrackerEntryForm
from .models import (
    AlternativeInvestmentItem,
    AltInvestmentStatus,
    ClientReport,
    IPSReviewEntry,
    Proposal,
    ProposalDocument,
    ProposalStatus,
    SelfGeneratedTarget,
    SharePointTrackerEntry,
    StatusPhase,
    TenderOutcomeUpdate,
    TenderReferralEntry,
)
from .permissions import (
    ADMIN_ACCESS_KEY,
    ALT_ADMIN_ACCESS_KEY,
    ALT_TEAM_ACCESS_KEY,
    TEAM_ACCESS_KEY,
    access_key_required,
    alt_access_key_required,
    alt_admin_required,
    is_alt_admin,
    is_ops_admin,
    ops_admin_required,
)
from .utils import (
    ALT_STATUS_PREVIEW_BY_INVESTMENT,
    alt_headline_color_for_text,
    alt_name_key,
    alt_preview_status_for_investment,
    build_grouped_progress,
    build_summary,
    load_alt_investment_detail_sections,
    split_alt_text_blocks,
    status_badge_class,
)
from .trail import build_change_details, log_dashboard_event
from crm.models import MeetingFeedbackSeenState, MeetingLog


QUARTER_OPTIONS = {
    "q1": "First Quarter",
    "q2": "Second Quarter",
    "q3": "Third Quarter",
}


def get_selected_quarter(request):
    quarter = request.session.get("operations_dashboard_quarter", "q1")
    return quarter if quarter in QUARTER_OPTIONS else "q1"


def actor_label(request, fallback_label):
    if request.user.is_authenticated:
        return request.user.get_username() or fallback_label
    return fallback_label


def get_quarterly_reports(quarter):
    if quarter in {"q2", "q3"}:
        quarter_reports = list(ClientReport.objects.filter(quarter=quarter).order_by("operations_assignee", "crm_name", "client_name"))
        if not quarter_reports:
            for report in ClientReport.objects.filter(quarter="q1").order_by("operations_assignee", "crm_name", "client_name"):
                ClientReport.objects.get_or_create(
                    quarter=quarter,
                    client_name=report.client_name,
                    defaults={
                        "crm_name": report.crm_name,
                        "operations_assignee": report.operations_assignee,
                        "due_date": report.due_date,
                        "status_phase": StatusPhase.PENDING,
                        "submitted_tick": False,
                        "reviewed_tick": False,
                        "sent_to_client_tick": False,
                        "notes": report.notes,
                    },
                )
        quarter_reports = list(ClientReport.objects.filter(quarter=quarter).order_by("operations_assignee", "crm_name", "client_name"))
        for report in quarter_reports:
            report.status_phase = StatusPhase.PENDING
            report.submitted_tick = False
            report.reviewed_tick = False
            report.sent_to_client_tick = False
        return quarter_reports

    return list(ClientReport.objects.filter(quarter=quarter).order_by("operations_assignee", "crm_name", "client_name"))


def filter_reports(reports, search_query="", status_filter=""):
    filtered = reports
    if search_query:
        filtered = [
            report
            for report in filtered
            if search_query.lower() in (report.client_name or "").lower()
            or search_query.lower() in (report.crm_name or "").lower()
            or search_query.lower() in (report.operations_assignee or "").lower()
        ]
    if status_filter:
        filtered = [report for report in filtered if report.status_phase == status_filter]
    return filtered
from .permissions import BD_ADMIN_ACCESS_KEY, BD_TEAM_ACCESS_KEY, bd_access_key_required, bd_admin_required, is_bd_admin



def consultancy_hub(request):
    def get_crm_meetings_unseen_count():
        access = request.session.get('crm_access') or {}
        if access.get('role') == 'owner' and access.get('owner'):
            viewer_name = access.get('owner')
        elif access.get('role') == 'admin':
            viewer_name = 'Admin'
        else:
            return 0

        state, _ = MeetingFeedbackSeenState.objects.get_or_create(viewer_name=viewer_name)
        meetings = MeetingLog.objects.all()
        if state.last_seen_at:
            meetings = meetings.filter(
                Q(created_at__gt=state.last_seen_at)
                | Q(created_at=state.last_seen_at, pk__gt=state.last_seen_meeting_pk)
            )
        return meetings.count()

    meetings_unseen_count = get_crm_meetings_unseen_count()

    dashboards = [
        {
            "name": "Operations Dashboard",
            "description": "Reporting tracker with operations workflow statuses.",
            "route": "unlock_access",
            "state": "live",
            "icon": "OPS",
        },
        {
            "name": "Client Relations Dashboard",
            "description": "CRM action items, live charts, and owner/admin controls.",
            "route": "crm:unlock_access",
            "meetings_route": "crm:meetings_unlock",
            "meetings_unseen_count": meetings_unseen_count,
            "state": "live",
            "icon": "CRM",
        },
        {
            "name": "Alternative Investments Dashboard",
            "description": "Alternative investment summary and detailed review tracking.",
            "route": "alt_investments_unlock",
            "state": "live",
            "icon": "ALT",
        },
        {
            "name": "Business Development Dashboard",
            "description": "Pipeline, opportunities, IPS reviews and tenders.",
            "route": "business_development_unlock",
            "state": "live",
            "icon": "BD",
        },
    ]
    return render(request, "reports/consultancy_hub.html", {"dashboards": dashboards})


def unlock_access(request):
    if request.method == "POST":
        passkey = request.POST.get("passkey", "")
        quarter = request.POST.get("quarter", "q1")
        quarter = quarter if quarter in QUARTER_OPTIONS else "q1"
        if passkey == ADMIN_ACCESS_KEY:
            request.session["access_key"] = ADMIN_ACCESS_KEY
            request.session["access_level"] = "admin"
            request.session["operations_dashboard_quarter"] = quarter
            messages.success(request, f"Admin passkey accepted. {QUARTER_OPTIONS[quarter]} selected.")
            return redirect("dashboard")
        if passkey == TEAM_ACCESS_KEY:
            request.session["access_key"] = TEAM_ACCESS_KEY
            request.session["access_level"] = "team"
            request.session["operations_dashboard_quarter"] = quarter
            messages.success(request, f"Team passkey accepted. {QUARTER_OPTIONS[quarter]} selected.")
            return redirect("dashboard")
        messages.error(request, "Invalid passkey.")

    current_level = request.session.get("access_level")
    selected_quarter = get_selected_quarter(request)
    intro_text = (
        "Operations Admin passkey is required to continue."
        if current_level == "admin"
        else "Operations Team passkey is required to continue."
    )
    return render(
        request,
        "reports/bd_unlock.html",
        {
            "page_title": "Unlock Operations Dashboard | IntelleGo",
            "heading": "Unlock Operations Dashboard",
            "intro_text": intro_text,
            "passkey_label": "Operations Passkey",
            "submit_label": "Unlock dashboard",
            "show_quarter_selector": True,
            "quarter_options": [
                {"value": "q1", "label": "First Quarter", "selected": selected_quarter == "q1"},
                {"value": "q2", "label": "Second Quarter", "selected": selected_quarter == "q2"},
                {"value": "q3", "label": "Third Quarter", "selected": selected_quarter == "q3"},
            ],
            "selected_quarter": selected_quarter,
        },
    )


def exit_access(request):
    request.session.flush()
    messages.success(request, "Session cleared. You have exited the dashboard.")
    return redirect("unlock_access")


@access_key_required
def dashboard(request):
    selected_quarter = get_selected_quarter(request)
    search_query = request.GET.get("q", "").strip()
    reports = get_quarterly_reports(selected_quarter)
    reports = filter_reports(reports, search_query=search_query)

    summary = build_summary(reports)
    crm_rows = build_grouped_progress("crm_name", reports)
    operations_rows = build_grouped_progress("operations_assignee", reports)
    chart_data = {
        "summary": {
            "pending": summary["pending_count"],
            "submitted": summary["submitted_count"],
            "reviewed": summary["reviewed_count"],
            "sent": summary["sent_count"],
        },
        "crm": {
            "labels": [row["name"] for row in crm_rows],
            "percent_done": [row["percent_done"] for row in crm_rows],
            "submitted": [row["submitted"] for row in crm_rows],
            "reviewed": [row["reviewed"] for row in crm_rows],
            "sent": [row["sent"] for row in crm_rows],
        },
    }
    return render(
        request,
        "reports/dashboard.html",
        {
            "summary": summary,
            "reports": reports,
            "crm_rows": crm_rows,
            "operations_rows": operations_rows,
            "search_query": search_query,
            "show_operations_section": is_ops_admin(request),
            "show_edit_actions": is_ops_admin(request),
            "status_badge_class": status_badge_class,
            "chart_data": chart_data,
            "selected_quarter": selected_quarter,
            "quarter_label": QUARTER_OPTIONS[selected_quarter],
        },
    )


@access_key_required
def report_tracker(request):
    selected_quarter = get_selected_quarter(request)
    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    reports = get_quarterly_reports(selected_quarter)
    reports = filter_reports(reports, search_query=search_query, status_filter=status_filter)

    return render(
        request,
        "reports/report_tracker.html",
        {
            "reports": reports,
            "search_query": search_query,
            "status_filter": status_filter,
            "status_badge_class": status_badge_class,
            "show_edit_actions": is_ops_admin(request),
            "selected_quarter": selected_quarter,
            "quarter_label": QUARTER_OPTIONS[selected_quarter],
        },
    )


@ops_admin_required
@access_key_required
def operations_staff_view(request):
    selected_quarter = get_selected_quarter(request)
    reports = get_quarterly_reports(selected_quarter)
    return render(
        request,
        "reports/operations_staff.html",
        {
            "operations_rows": build_grouped_progress("operations_assignee", reports),
            "status_badge_class": status_badge_class,
            "selected_quarter": selected_quarter,
            "quarter_label": QUARTER_OPTIONS[selected_quarter],
        },
    )


@ops_admin_required
@access_key_required
def edit_report(request, pk):
    report = get_object_or_404(ClientReport, pk=pk)
    if request.method == "POST":
        form = ReportStatusForm(request.POST, instance=report)
        if form.is_valid():
            details = build_change_details(
                form,
                {
                    "status_phase": "Status Phase",
                    "submitted_tick": "Submitted",
                    "reviewed_tick": "Reviewed",
                    "sent_to_client_tick": "Sent to Client",
                    "due_date": "Due Date",
                    "notes": "Notes",
                },
            )
            form.save()
            event_type = "status_changed" if "status_phase" in form.changed_data else "updated"
            log_dashboard_event(
                dashboard_key="operations",
                event_type=event_type,
                section_label="Report Tracker",
                record_label=report.client_name,
                summary=f"Updated report for {report.client_name}.",
                details=details,
                actor_label=actor_label(request, "Operations Admin"),
            )
            messages.success(request, f"Updated {report.client_name}.")
            return redirect("report_tracker")
    else:
        form = ReportStatusForm(instance=report)

    return render(request, "reports/report_form.html", {"form": form, "report": report})


@access_key_required
def sharepoint_tracker(request):
    selected_quarter = get_selected_quarter(request)
    if selected_quarter == "q1" and not SharePointTrackerEntry.objects.filter(quarter="q1").exists():
        call_command("import_sharepoint_tracker")

    if selected_quarter in {"q2", "q3"}:
        q1_entries = list(SharePointTrackerEntry.objects.filter(quarter="q1"))
        if not SharePointTrackerEntry.objects.filter(quarter=selected_quarter).exists():
            for entry in q1_entries:
                SharePointTrackerEntry.objects.get_or_create(
                    quarter=selected_quarter,
                    client_name=entry.client_name,
                    defaults={
                        "crm_name": entry.crm_name,
                        "alternate_name": entry.alternate_name,
                        "word_submitted": entry.word_submitted,
                        "excel_submitted": entry.excel_submitted,
                        "pdf_submitted": entry.pdf_submitted,
                        "due_date": entry.due_date,
                        "notes": entry.notes,
                    },
                )

    search_query = request.GET.get("q", "").strip()
    entries = list(SharePointTrackerEntry.objects.filter(quarter=selected_quarter))

    for entry in entries:
        entry.sync_status()
        entry.save(update_fields=["status"])

    if search_query:
        entries = [
            entry
            for entry in entries
            if search_query.lower() in (entry.client_name or "").lower()
            or search_query.lower() in (entry.crm_name or "").lower()
            or search_query.lower() in (entry.alternate_name or "").lower()
            or search_query.lower() in (entry.notes or "").lower()
        ]

    return render(
        request,
        "reports/sharepoint_tracker.html",
        {
            "entries": entries,
            "search_query": search_query,
            "show_edit_actions": is_ops_admin(request),
            "selected_quarter": selected_quarter,
            "quarter_label": QUARTER_OPTIONS[selected_quarter],
        },
    )


@ops_admin_required
@access_key_required
def edit_sharepoint_entry(request, pk):
    entry = get_object_or_404(SharePointTrackerEntry, pk=pk)
    if request.method == "POST":
        form = SharePointTrackerEntryForm(request.POST, instance=entry)
        if form.is_valid():
            details = build_change_details(
                form,
                {
                    "client_name": "Client",
                    "crm_name": "CRM",
                    "alternate_name": "Alternate Name",
                    "word_submitted": "Word Submitted",
                    "excel_submitted": "Excel Submitted",
                    "pdf_submitted": "PDF Submitted",
                    "due_date": "Due Date",
                    "status": "Status",
                    "notes": "Notes",
                },
            )
            form.save()
            event_type = "status_changed" if "status" in form.changed_data else "updated"
            log_dashboard_event(
                dashboard_key="operations",
                event_type=event_type,
                section_label="SharePoint Tracker",
                record_label=entry.client_name,
                summary=f"Updated SharePoint tracker entry for {entry.client_name}.",
                details=details,
                actor_label=actor_label(request, "Operations Admin"),
            )
            messages.success(request, f"Updated {entry.client_name}.")
            return redirect("sharepoint_tracker")
    else:
        form = SharePointTrackerEntryForm(instance=entry)

    return render(request, "reports/sharepoint_entry_form.html", {"form": form, "entry": entry})


@ops_admin_required
@access_key_required
def delete_sharepoint_entry(request, pk):
    entry = get_object_or_404(SharePointTrackerEntry, pk=pk)
    if request.method == "POST":
        record_label = entry.client_name
        entry.delete()
        log_dashboard_event(
            dashboard_key="operations",
            event_type="deleted",
            section_label="SharePoint Tracker",
            record_label=record_label,
            summary=f"Deleted SharePoint tracker entry for {record_label}.",
            details="Record removed from SharePoint tracker.",
            actor_label=actor_label(request, "Operations Admin"),
        )
        messages.success(request, f"Deleted {entry.client_name}.")
        return redirect("sharepoint_tracker")
    return redirect("sharepoint_tracker")


def alt_investments_unlock(request):
    if request.method == "POST":
        passkey = request.POST.get("passkey", "")
        if passkey == ALT_ADMIN_ACCESS_KEY:
            request.session["alt_access_key"] = ALT_ADMIN_ACCESS_KEY
            request.session["alt_access_level"] = "admin"
            messages.success(request, "Alternative Investments admin access granted.")
            return redirect("alt_investments_dashboard")
        if passkey == ALT_TEAM_ACCESS_KEY:
            request.session["alt_access_key"] = ALT_TEAM_ACCESS_KEY
            request.session["alt_access_level"] = "member"
            messages.success(request, "Alternative Investments access granted.")
            return redirect("alt_investments_dashboard")
        messages.error(request, "Invalid Alternative Investments passkey.")

    return render(
        request,
        "reports/bd_unlock.html",
        {
            "page_title": "Unlock Alternative Investments | IntelleGo",
            "heading": "Unlock Alternative Investments Dashboard",
            "intro_text": "Use the Alternative Investments passkey to continue.",
            "passkey_label": "Alternative Investments Passkey",
            "submit_label": "Unlock dashboard",
        },
    )


def business_development_unlock(request):
    if request.method == "POST":
        passkey = request.POST.get("passkey", "")
        if passkey == BD_ADMIN_ACCESS_KEY:
            request.session["bd_access_key"] = BD_ADMIN_ACCESS_KEY
            request.session["bd_access_level"] = "admin"
            messages.success(request, "Admin passkey accepted. Business Development unlocked.")
            return redirect("business_development_dashboard")
        if passkey == BD_TEAM_ACCESS_KEY:
            request.session["bd_access_key"] = BD_TEAM_ACCESS_KEY
            request.session["bd_access_level"] = "team"
            messages.success(request, "Viewer passkey accepted. Business Development unlocked.")
            return redirect("business_development_dashboard")
        messages.error(request, "Invalid passkey.")

    return render(
        request,
        "reports/bd_unlock.html",
        {
            "page_title": "Unlock Business Development | IntelleGo",
            "heading": "Unlock Business Development Dashboard",
            "intro_text": "Use the viewer passkey to view records or the admin passkey for full edit access.",
            "passkey_label": "Business Development Passkey",
            "submit_label": "Unlock dashboard",
        },
    )


def business_development_exit(request):
    request.session.pop("bd_access_key", None)
    request.session.pop("bd_access_level", None)
    messages.success(request, "You exited Business Development dashboard.")
    return redirect("business_development_unlock")


@bd_access_key_required
def business_development_dashboard(request):
    ips = list(IPSReviewEntry.objects.all().order_by("fund_name"))

    def status_label(row):
        status_text = (row.status_comments or "").lower()
        if "signed" in status_text:
            return "Signed"
        if "draft" in status_text:
            return "Draft"
        if "in progress" in status_text:
            return "In Progress"
        return "Other"

    status_order = {"Signed": 0, "Draft": 1, "In Progress": 2, "Other": 3}
    for row in ips:
        row.status_bucket = status_label(row)
        row.status_rank = status_order[row.status_bucket]

    ips_rows = sorted(ips, key=lambda row: (row.status_rank, row.fund_name or ""))

    def percentage(count, total):
        return round((count / total) * 100, 1) if total else 0.0

    document_fields = [
        ("member_fin_schedules", "Member Fin. Schedules"),
        ("financial_review", "Financial Review"),
        ("replacement_ratios", "Replacement Ratios"),
        ("date_data_received", "Date Data Received"),
        ("date_sent_to_client", "Date Sent to Client"),
        ("workshop_required", "Workshop Required"),
        ("asset_mgr_mandates", "Asset Mgr Mandates"),
    ]
    doc_completion = []
    for field_name, label in document_fields:
        if field_name in {"replacement_ratios", "asset_mgr_mandates"}:
            complete = sum(1 for row in ips if getattr(row, field_name, "").strip() not in {"", "-"})
        else:
            complete = sum(1 for row in ips if getattr(row, field_name))
        doc_completion.append(
            {
                "label": label,
                "complete": complete,
                "total": len(ips),
                "percent": percentage(complete, len(ips)),
            }
        )

    status_keywords = ["signed", "draft", "in progress"]
    status_breakdown = []
    for keyword in status_keywords:
        status_breakdown.append(
            {
                "label": keyword.title(),
                "count": sum(1 for row in ips if keyword in (row.status_comments or "").lower()),
            }
        )

    def top_counts(items, attr):
        counts = {}
        for item in items:
            value = getattr(item, attr, "") or "Unassigned"
            counts[value] = counts.get(value, 0) + 1
        return sorted(({"label": key, "count": value} for key, value in counts.items()), key=lambda x: (-x["count"], x["label"]))[:6]

    crm_workload = {
        "ic_crm": top_counts(ips, "ic_crm"),
        "admin_crm": top_counts(ips, "admin_crm"),
    }

    return render(
        request,
        "reports/business_development_dashboard.html",
        {
            "ips_count": len(ips),
            "dashboard_total_funds": len(ips),
            "dashboard_ips_signed": sum(1 for row in ips if "signed" in (row.status_comments or "").lower()),
            "asset_manager_mandates_outstanding": sum(1 for row in ips if (row.asset_mgr_mandates or "").strip().lower() == "outstanding"),
            "dashboard_completion_rate": percentage(sum(1 for row in ips if row.member_fin_schedules and row.financial_review and row.replacement_ratios), len(ips)),
            "doc_completion": doc_completion,
            "status_breakdown": status_breakdown,
            "crm_workload": crm_workload,
            "ips_rows": ips_rows,
            "is_bd_admin": is_bd_admin(request),
        },
    )


@bd_access_key_required
def ips_reviews_list(request):
    rows = IPSReviewEntry.objects.all().order_by("fund_name")
    return render(request, "reports/ips_reviews_list.html", {"rows": rows, "is_bd_admin": is_bd_admin(request)})


@bd_access_key_required
def tenders_list(request):
    rows = TenderReferralEntry.objects.all().order_by("source_section", "client_name")
    tender_updates = TenderOutcomeUpdate.objects.select_related("tender").order_by("-updated_at", "-created_at")

    latest_update_by_tender = {}
    for update in tender_updates:
        latest_update_by_tender.setdefault(update.tender_id, update)

    sections = {}
    for row in rows:
        latest_update = latest_update_by_tender.get(row.pk)
        if latest_update:
            row.current_outcome_status = latest_update.outcome_status
            row.current_outcome_update = latest_update.outcome_update
            row.current_outcome_badge_class = latest_update.outcome_badge_class
        else:
            row.current_outcome_status = row.get_outcome_status_display()
            row.current_outcome_update = row.outcome_update
            row.current_outcome_badge_class = row.outcome_badge_class
        section = (row.source_section or "Unsectioned").strip()
        sections.setdefault(section, []).append(row)

    return render(
        request,
        "reports/tenders_list.html",
        {
            "sections": sections,
            "is_bd_admin": is_bd_admin(request),
            "tender_updates": tender_updates,
        },
    )


@bd_access_key_required
@bd_admin_required
def tender_update_add(request):
    from .forms import TenderOutcomeUpdateForm

    if request.method == "POST":
        form = TenderOutcomeUpdateForm(request.POST)
        if form.is_valid():
            update = form.save()
            tender = update.tender
            tender.outcome_status = update.outcome_status
            tender.outcome_update = update.outcome_update
            tender.save(update_fields=["outcome_status", "outcome_update", "updated_at"])
            log_dashboard_event(
                dashboard_key="business_development",
                event_type="status_changed",
                section_label="Tender Updates",
                record_label=tender.client_name,
                summary=f"Added tender outcome update for {tender.client_name}.",
                details=f"Outcome set to {update.get_outcome_status_display()}. Update: {update.outcome_update or '-'}",
                actor_label=actor_label(request, "BD Admin"),
            )
            messages.success(request, "Tender update added.")
            return redirect("tenders_list")
    else:
        form = TenderOutcomeUpdateForm()
    return render(request, "reports/tender_update_form.html", {"form": form})


@bd_access_key_required
@bd_admin_required
def tender_update_edit(request, pk):
    from .forms import TenderOutcomeUpdateForm

    obj = get_object_or_404(TenderOutcomeUpdate, pk=pk)
    if request.method == "POST":
        form = TenderOutcomeUpdateForm(request.POST, instance=obj)
        if form.is_valid():
            details = build_change_details(
                form,
                {
                    "tender": "Tender",
                    "outcome_status": "Outcome Status",
                    "outcome_update": "Outcome Update",
                },
            )
            update = form.save()
            tender = update.tender
            tender.outcome_status = update.outcome_status
            tender.outcome_update = update.outcome_update
            tender.save(update_fields=["outcome_status", "outcome_update", "updated_at"])
            log_dashboard_event(
                dashboard_key="business_development",
                event_type="status_changed",
                section_label="Tender Updates",
                record_label=tender.client_name,
                summary=f"Edited tender outcome update for {tender.client_name}.",
                details=details,
                actor_label=actor_label(request, "BD Admin"),
            )
            messages.success(request, "Tender update edited.")
            return redirect("tenders_list")
    else:
        form = TenderOutcomeUpdateForm(instance=obj)
    return render(request, "reports/tender_update_form.html", {"form": form, "obj": obj})


@bd_access_key_required
@bd_admin_required
def tender_update_delete(request, pk):
    obj = get_object_or_404(TenderOutcomeUpdate, pk=pk)
    if request.method == "POST":
        record_label = obj.tender.client_name
        obj.delete()
        log_dashboard_event(
            dashboard_key="business_development",
            event_type="deleted",
            section_label="Tender Updates",
            record_label=record_label,
            summary=f"Deleted tender outcome update for {record_label}.",
            details="A tender outcome update entry was removed.",
            actor_label=actor_label(request, "BD Admin"),
        )
        messages.success(request, "Tender update deleted.")
        return redirect("tenders_list")
    return render(request, "reports/tender_update_delete_confirm.html", {"obj": obj})


@bd_access_key_required
def self_generated_list(request):
    rows = SelfGeneratedTarget.objects.all().order_by("source_section", "client_name")

    sections = {}
    for row in rows:
        section = (row.source_section or "Unsectioned").strip()
        sections.setdefault(section, []).append(row)

    return render(request, "reports/self_generated_list.html", {"sections": sections, "is_bd_admin": is_bd_admin(request)})


@bd_access_key_required
@bd_admin_required
def ips_review_add(request):
    from .forms import IPSReviewEntryForm

    if request.method == "POST":
        form = IPSReviewEntryForm(request.POST)
        if form.is_valid():
            item = form.save()
            log_dashboard_event(
                dashboard_key="business_development",
                event_type="created",
                section_label="IPS Reviews",
                record_label=item.fund_name,
                summary=f"Added new IPS review for {item.fund_name}.",
                details=f"IC CRM: {item.ic_crm or '-'}; Admin CRM: {item.admin_crm or '-'}",
                actor_label=actor_label(request, "BD Admin"),
            )
            messages.success(request, "IPS review added.")
            return redirect("ips_reviews_list")
    else:
        form = IPSReviewEntryForm()
    return render(request, "reports/ips_review_form.html", {"form": form})


@bd_access_key_required
@bd_admin_required
def ips_review_delete(request, pk):
    obj = get_object_or_404(IPSReviewEntry, pk=pk)
    if request.method == "POST":
        fund = obj.fund_name
        obj.delete()
        log_dashboard_event(
            dashboard_key="business_development",
            event_type="deleted",
            section_label="IPS Reviews",
            record_label=fund,
            summary=f"Deleted IPS review for {fund}.",
            details="IPS review record removed.",
            actor_label=actor_label(request, "BD Admin"),
        )
        messages.success(request, f"Deleted {fund}.")
        return redirect("ips_reviews_list")
    return render(request, "reports/ips_review_delete_confirm.html", {"obj": obj})


@bd_access_key_required
@bd_admin_required
def ips_review_edit(request, pk):
    from .forms import IPSReviewEntryForm

    obj = get_object_or_404(IPSReviewEntry, pk=pk)
    if request.method == "POST":
        form = IPSReviewEntryForm(request.POST, instance=obj)
        if form.is_valid():
            details = build_change_details(form)
            form.save()
            log_dashboard_event(
                dashboard_key="business_development",
                event_type="updated",
                section_label="IPS Reviews",
                record_label=obj.fund_name,
                summary=f"Updated IPS review for {obj.fund_name}.",
                details=details,
                actor_label=actor_label(request, "BD Admin"),
            )
            messages.success(request, "IPS review updated.")
            return redirect("ips_reviews_list")
    else:
        form = IPSReviewEntryForm(instance=obj)
    return render(request, "reports/ips_review_form.html", {"form": form, "obj": obj})


@bd_access_key_required
@bd_admin_required
def tender_add(request):
    from .forms import TenderReferralEntryForm

    if request.method == "POST":
        form = TenderReferralEntryForm(request.POST)
        if form.is_valid():
            item = form.save()
            log_dashboard_event(
                dashboard_key="business_development",
                event_type="created",
                section_label="Tenders & Referrals",
                record_label=item.client_name,
                summary=f"Added new tender/referral for {item.client_name}.",
                details=f"Outcome status: {item.get_outcome_status_display()}",
                actor_label=actor_label(request, "BD Admin"),
            )
            messages.success(request, "Tender/Referral added.")
            return redirect("tenders_list")
    else:
        form = TenderReferralEntryForm()
    return render(request, "reports/tender_form.html", {"form": form})


@bd_access_key_required
@bd_admin_required
def tender_edit(request, pk):
    from .forms import TenderReferralEntryForm

    obj = get_object_or_404(TenderReferralEntry, pk=pk)
    if request.method == "POST":
        form = TenderReferralEntryForm(request.POST, instance=obj)
        if form.is_valid():
            details = build_change_details(form)
            form.save()
            event_type = "status_changed" if "outcome_status" in form.changed_data else "updated"
            log_dashboard_event(
                dashboard_key="business_development",
                event_type=event_type,
                section_label="Tenders & Referrals",
                record_label=obj.client_name,
                summary=f"Updated tender/referral for {obj.client_name}.",
                details=details,
                actor_label=actor_label(request, "BD Admin"),
            )
            messages.success(request, "Tender/Referral updated.")
            return redirect("tenders_list")
    else:
        form = TenderReferralEntryForm(instance=obj)
    return render(request, "reports/tender_form.html", {"form": form, "obj": obj})


@bd_access_key_required
@bd_admin_required
def tender_delete(request, pk):
    obj = get_object_or_404(TenderReferralEntry, pk=pk)
    if request.method == "POST":
        client_name = obj.client_name
        obj.delete()
        log_dashboard_event(
            dashboard_key="business_development",
            event_type="deleted",
            section_label="Tenders & Referrals",
            record_label=client_name,
            summary=f"Deleted tender/referral record for {client_name}.",
            details="Tender/referral record removed.",
            actor_label=actor_label(request, "BD Admin"),
        )
        messages.success(request, f"Deleted {client_name}.")
        return redirect(reverse("tenders_list") + "#tenders")
    return render(request, "reports/tender_delete_confirm.html", {"obj": obj})


@bd_access_key_required
@bd_admin_required
def target_add(request):
    from .forms import SelfGeneratedTargetForm

    if request.method == "POST":
        form = SelfGeneratedTargetForm(request.POST)
        if form.is_valid():
            item = form.save()
            log_dashboard_event(
                dashboard_key="business_development",
                event_type="created",
                section_label="Self-Generated Targets",
                record_label=item.client_name,
                summary=f"Added self-generated target for {item.client_name}.",
                details=f"Business target: {item.business_target or '-'}",
                actor_label=actor_label(request, "BD Admin"),
            )
            messages.success(request, "Self-generated target added.")
            return redirect(reverse("self_generated_list") + "#targets")
    else:
        form = SelfGeneratedTargetForm()
    return render(request, "reports/target_form.html", {"form": form})


@bd_access_key_required
@bd_admin_required
def target_edit(request, pk):
    from .forms import SelfGeneratedTargetForm

    obj = get_object_or_404(SelfGeneratedTarget, pk=pk)
    if request.method == "POST":
        form = SelfGeneratedTargetForm(request.POST, instance=obj)
        if form.is_valid():
            details = build_change_details(form)
            form.save()
            log_dashboard_event(
                dashboard_key="business_development",
                event_type="updated",
                section_label="Self-Generated Targets",
                record_label=obj.client_name,
                summary=f"Updated self-generated target for {obj.client_name}.",
                details=details,
                actor_label=actor_label(request, "BD Admin"),
            )
            messages.success(request, "Self-generated target updated.")
            return redirect(reverse("self_generated_list") + "#targets")
    else:
        form = SelfGeneratedTargetForm(instance=obj)
    return render(request, "reports/target_form.html", {"form": form, "obj": obj})


@bd_access_key_required
@bd_admin_required
def target_delete(request, pk):
    obj = get_object_or_404(SelfGeneratedTarget, pk=pk)
    if request.method == "POST":
        client_name = obj.client_name
        obj.delete()
        log_dashboard_event(
            dashboard_key="business_development",
            event_type="deleted",
            section_label="Self-Generated Targets",
            record_label=client_name,
            summary=f"Deleted self-generated target for {client_name}.",
            details="Self-generated target record removed.",
            actor_label=actor_label(request, "BD Admin"),
        )
        messages.success(request, f"Deleted {client_name}.")
        return redirect(reverse("self_generated_list") + "#targets")
    return render(request, "reports/target_delete_confirm.html", {"obj": obj})


def alt_investments_exit(request):
    request.session.pop("alt_access_key", None)
    request.session.pop("alt_access_level", None)
    messages.success(request, "You exited the Alternative Investments dashboard.")
    return redirect("alt_investments_unlock")


ALT_RISK_BY_INVESTMENT = {
    "Fairview Stands – Residential Development": "Moderate",
    "Baines Intercare – Emergency Clinic / Hospital": "Moderate",
    "Sanganayi Food Court": "High",
    "Tanganda Road Motel t/a Palm Tree Place": "Moderate",
    "Golden Leaf Warehouse": "Moderate",
    "Invesci Residential Property Fund": "Low",
    "Main Street Medical Centre (Bindura Medi Clinic)": "Low",
    "Datlabs (Private) Limited": "High",
    "159 Second Street (Wellpage Office Building)": "Moderate",
    "Mangwana Opportunities Fund": "High",
    "Smart Suburbs Property Project": "Moderate",
    "Northwest High School": "High",
    "Hanzu Resources": "High",
    "Mandara Cluster Development": "Moderate",
    "Redd Optics Laboratories": "High",
    "Chegutu Housing Development": "Moderate",
    "Cicada Farming / Agrowth Farming (ZAM)": "Moderate",
    "Bulawayo Student Accommodation (Zimcampus)": "High",
    "Brick n Mortar Fund (Tynwald Development Project)": "Moderate",
    "Harava Solar Park (Pvt) Ltd": "High",
    "Nhaka Beef – Cattle Investment": "Moderate",
    "Mbano Manor Hotel": "High",
}

def _alt_preview_status_for_item(item):
    return item.status_headline.strip() or alt_preview_status_for_investment(item.investment_name, item.summary_update)


def _alt_preview_headline_css_for_item(item):
    if item.status_headline_color == AltInvestmentStatus.GREEN:
        return "bg-emerald-100 text-emerald-800"
    if item.status_headline_color == AltInvestmentStatus.RED:
        return "bg-rose-100 text-rose-800"
    return "bg-amber-100 text-amber-800"


def _alt_preview_css_for_item(item):
    inferred_color = item.status_headline_color or alt_headline_color_for_text(_alt_preview_status_for_item(item), item.status)
    if inferred_color == AltInvestmentStatus.GREEN:
        return "bg-emerald-100 text-emerald-800"
    if inferred_color == AltInvestmentStatus.RED:
        return "bg-rose-100 text-rose-800"
    return "bg-amber-100 text-amber-800"


def _build_alt_rows(items):
    rows = []
    for item in items:
        rows.append(
            {
                "item": item,
                "risk": item.risk or ALT_RISK_BY_INVESTMENT.get(item.investment_name, "-"),
                "status_preview": _alt_preview_status_for_item(item),
                "status_preview_css": _alt_preview_headline_css_for_item(item),
            }
        )
    return rows


def _build_alt_detail_panels(item):
    document_sections = load_alt_investment_detail_sections().get(alt_name_key(item.investment_name), {})

    def resolve_lines(key, fallback_text):
        lines = split_alt_text_blocks(getattr(item, key, "")) or document_sections.get(key) or split_alt_text_blocks(fallback_text)
        if lines:
            return lines
        return ["No information available."]

    panels = [
        {
            "title": "Investment Details",
            "lines": resolve_lines("investment_details", item.detailed_review or item.summary_update),
        },
        {
            "title": "Pension Funds Invested",
            "lines": resolve_lines("pension_funds_invested", item.summary_update),
        },
        {
            "title": "Status & Developments",
            "lines": resolve_lines("status_developments", item.summary_update),
        },
        {
            "title": "Performance",
            "lines": resolve_lines("performance", item.summary_update or item.detailed_review),
        },
    ]

    for panel in panels:
        panel["headline"] = panel["lines"][0] if panel["lines"] else ""
        panel["bullets"] = panel["lines"][1:] if len(panel["lines"]) > 1 else []

    return panels


def _alt_detail_headline(item):
    return item.status_headline.strip() or alt_preview_status_for_investment(item.investment_name, item.summary_update)


def _alt_detail_headline_css(item):
    return _alt_preview_headline_css_for_item(item)


@alt_access_key_required
def proposals_list(request):
    proposals = Proposal.objects.select_related("created_by").all()
    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search_query:
        proposals = proposals.filter(
            Q(proposal_name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(created_by__username__icontains=search_query)
        )
    if status_filter:
        proposals = proposals.filter(status=status_filter)

    proposals = proposals.order_by("-date", "proposal_name")

    paginator = Paginator(proposals, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "reports/proposals_list.html",
        {
            "page_obj": page_obj,
            "search_query": search_query,
            "status_filter": status_filter,
            "status_choices": [
                ("", "All status"),
                (ProposalStatus.RECEIVED, "Received"),
                (ProposalStatus.PRELIMINARY, "Preliminary analysis done"),
                (ProposalStatus.UNDER_REVIEW, "Under review"),
                (ProposalStatus.FINALISED, "Finalised"),
                (ProposalStatus.APPROVED, "Approved"),
                (ProposalStatus.DECLINED, "Declined"),
            ],
            "is_alt_admin": is_alt_admin(request),
            "hide_global_nav": True,
        },
    )


@alt_access_key_required
def proposal_detail(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    documents = proposal.documents.all()
    return render(
        request,
        "reports/proposal_detail.html",
        {
            "proposal": proposal,
            "documents": documents,
            "is_alt_admin": is_alt_admin(request),
            "hide_global_nav": True,
        },
    )


@alt_access_key_required
@alt_admin_required
def proposal_add(request):
    if request.method == "POST":
        proposal = Proposal()
        if request.user.is_authenticated:
            proposal.created_by = request.user
        form = ProposalForm(request.POST, instance=proposal)
        if form.is_valid():
            created = form.save()
            log_dashboard_event(
                dashboard_key="alternative_investments",
                event_type="created",
                section_label="Proposals",
                record_label=created.proposal_name,
                summary=f"Added proposal: {created.proposal_name}.",
                details=f"Status: {created.get_status_display()}",
                actor_label=actor_label(request, "Alternative Investments Admin"),
            )
            messages.success(request, "Proposal added successfully.")
            return redirect("proposals_list")
    else:
        form = ProposalForm()

    return render(
        request,
        "reports/proposal_form.html",
        {
            "form": form,
            "page_title": "Add Proposal",
            "is_alt_admin": True,
            "hide_global_nav": True,
        },
    )


@alt_access_key_required
@alt_admin_required
def proposal_edit(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    if request.method == "POST":
        form = ProposalForm(request.POST, instance=proposal)
        if form.is_valid():
            details = build_change_details(form, {"proposal_name": "Proposal Name", "date": "Date", "status": "Status", "description": "Description"})
            form.save()
            event_type = "status_changed" if "status" in form.changed_data else "updated"
            log_dashboard_event(
                dashboard_key="alternative_investments",
                event_type=event_type,
                section_label="Proposals",
                record_label=proposal.proposal_name,
                summary=f"Updated proposal: {proposal.proposal_name}.",
                details=details,
                actor_label=actor_label(request, "Alternative Investments Admin"),
            )
            messages.success(request, "Proposal updated successfully.")
            return redirect("proposal_detail", pk=proposal.pk)
    else:
        form = ProposalForm(instance=proposal)

    return render(
        request,
        "reports/proposal_form.html",
        {
            "form": form,
            "page_title": "Edit Proposal",
            "proposal": proposal,
            "is_alt_admin": True,
            "hide_global_nav": True,
        },
    )


@alt_access_key_required
@alt_admin_required
def proposal_delete(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    if request.method == "POST":
        proposal_name = proposal.proposal_name
        proposal.delete()
        log_dashboard_event(
            dashboard_key="alternative_investments",
            event_type="deleted",
            section_label="Proposals",
            record_label=proposal_name,
            summary=f"Deleted proposal: {proposal_name}.",
            details="Proposal record removed.",
            actor_label=actor_label(request, "Alternative Investments Admin"),
        )
        messages.success(request, "Proposal deleted successfully.")
        return redirect("proposals_list")
    return render(
        request,
        "reports/proposal_confirm_delete.html",
        {"proposal": proposal, "is_alt_admin": True, "hide_global_nav": True},
    )


@alt_access_key_required
@alt_admin_required
def proposal_document_upload(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    if request.method == "POST":
        files = request.FILES.getlist("files")
        if not files:
            messages.error(request, "No documents were selected.")
            return redirect("proposal_detail", pk=proposal.pk)
        for uploaded_file in files:
            ProposalDocument.objects.create(
                proposal=proposal,
                file=uploaded_file,
                document_name=uploaded_file.name,
            )
        log_dashboard_event(
            dashboard_key="alternative_investments",
            event_type="updated",
            section_label="Proposal Documents",
            record_label=proposal.proposal_name,
            summary=f"Uploaded {len(files)} document(s) to {proposal.proposal_name}.",
            details=", ".join(uploaded_file.name for uploaded_file in files[:6]),
            actor_label=actor_label(request, "Alternative Investments Admin"),
        )
        messages.success(request, f"{len(files)} document(s) uploaded successfully.")
        return redirect("proposal_detail", pk=proposal.pk)
    return redirect("proposal_detail", pk=proposal.pk)


@alt_access_key_required
@alt_admin_required
def proposal_document_delete(request, pk):
    document = get_object_or_404(ProposalDocument, pk=pk)
    proposal = document.proposal
    if request.method == "POST":
        document_name = document.document_name or document.file.name
        document.delete()
        log_dashboard_event(
            dashboard_key="alternative_investments",
            event_type="deleted",
            section_label="Proposal Documents",
            record_label=proposal.proposal_name,
            summary=f"Deleted document from {proposal.proposal_name}.",
            details=document_name,
            actor_label=actor_label(request, "Alternative Investments Admin"),
        )
        messages.success(request, "Document deleted successfully.")
        return redirect("proposal_detail", pk=proposal.pk)
    return render(
        request,
        "reports/proposal_document_confirm_delete.html",
        {"document": document, "proposal": proposal, "is_alt_admin": True, "hide_global_nav": True},
    )


@alt_access_key_required
def alt_investments_dashboard(request):
    items = AlternativeInvestmentItem.objects.all().order_by("id")
    rows = _build_alt_rows(items)

    # compute counts from data but allow admin override for labels/values
    status_previews = [row["status_preview"] for row in rows]
    computed_distressed = sum(
        1
        for text in status_previews
        if "DISTRESSED" in text or "ON HOLD" in text or "TROUBLED" in text
    )
    computed_best = sum(
        1
        for text in status_previews
        if text in {
            "ABOVE TARGET – STRONG PERFORMANCE",
            "PERFORMING WELL ABOVE TARGET",
            "BEST-IN-CLASS – CONSISTENT 12% RETURN",
        }
    )

    from .models import DashboardSettings

    settings_obj = DashboardSettings.get_solo()

    if is_alt_admin(request) and request.method == "POST":
        form = DashboardSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            details = build_change_details(form, {
                "manager_count_label": "Asset Managers",
                "pension_funds_label": "Pension Funds",
                "best_performers": "Best Performers",
                "distressed_count": "On Hold / Distressed",
            })
            form.save()
            log_dashboard_event(
                dashboard_key="alternative_investments",
                event_type="updated",
                section_label="Summary Banner",
                record_label="Dashboard Summary",
                summary="Updated alternative investments summary banner.",
                details=details,
                actor_label=actor_label(request, "Alternative Investments Admin"),
            )
            messages.success(request, "Dashboard summary updated.")
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "ok": True,
                    "manager_count_label": settings_obj.manager_count_label,
                    "pension_funds_label": settings_obj.pension_funds_label,
                    "best_performers": settings_obj.best_performers,
                    "distressed_count": settings_obj.distressed_count,
                })
            return redirect("alt_investments_dashboard")
    else:
        form = DashboardSettingsForm(instance=settings_obj) if is_alt_admin(request) else None

    summary = {
        "total": items.count(),
        "manager_count_label": settings_obj.manager_count_label,
        "pension_funds_label": settings_obj.pension_funds_label,
        "best_performers": settings_obj.best_performers or computed_best,
        "distressed_count": settings_obj.distressed_count or computed_distressed,
    }

    return render(
        request,
        "reports/alt_investments_dashboard.html",
        {
            "summary": summary,
            "rows": rows,
            "is_alt_admin": is_alt_admin(request),
            "dashboard_form": form,
            "hide_global_nav": True,
        },
    )


@alt_access_key_required
def alt_investment_detail(request, pk):
    item = get_object_or_404(AlternativeInvestmentItem, pk=pk)
    detail_meta = load_alt_investment_detail_sections().get(alt_name_key(item.investment_name), {})
    form = None

    if is_alt_admin(request):
        if request.method == "POST":
            form = AlternativeInvestmentItemForm(request.POST, instance=item)
            if form.is_valid():
                details = build_change_details(form)
                form.save()
                event_type = "status_changed" if "status" in form.changed_data else "updated"
                log_dashboard_event(
                    dashboard_key="alternative_investments",
                    event_type=event_type,
                    section_label="Investment Reviews",
                    record_label=item.investment_name,
                    summary=f"Updated investment details for {item.investment_name}.",
                    details=details,
                    actor_label=actor_label(request, "Alternative Investments Admin"),
                )
                messages.success(request, f"Updated {item.investment_name}.")
                return redirect("alt_investment_detail", pk=item.pk)
            else:
                messages.error(request, "Save failed — see server logs for details.")
        else:
            form = AlternativeInvestmentItemForm(instance=item)

    return render(
        request,
        "reports/alt_investment_detail.html",
        {
            "item": item,
            "detail_meta": detail_meta,
            "status_headline": _alt_detail_headline(item),
            "status_headline_css": _alt_detail_headline_css(item),
            "panels": _build_alt_detail_panels(item),
            "is_alt_admin": is_alt_admin(request),
            "form": form,
            "hide_global_nav": True,
        },
    )


@alt_access_key_required
def alt_investments_reviews(request):
    items = AlternativeInvestmentItem.objects.all().order_by("id")
    status_filter = request.GET.get("status", "").strip()
    search_query = request.GET.get("q", "").strip()
    if status_filter in AltInvestmentStatus.values:
        items = items.filter(status=status_filter)
    if search_query:
        items = items.filter(
            Q(investment_name__icontains=search_query)
            | Q(category__icontains=search_query)
            | Q(owner__icontains=search_query)
            | Q(summary_update__icontains=search_query)
            | Q(detailed_review__icontains=search_query)
        )

    rows = _build_alt_rows(items)

    return render(
        request,
        "reports/alt_investments_reviews.html",
        {
            "rows": rows,
            "status_filter": status_filter,
            "search_query": search_query,
            "is_alt_admin": is_alt_admin(request),
            "hide_global_nav": True,
            "status_choices": [
                ("", "All status"),
                (AltInvestmentStatus.GREEN, "Green / On Track"),
                (AltInvestmentStatus.AMBER, "Amber / Watch"),
                (AltInvestmentStatus.RED, "Red / Critical"),
            ],
        },
    )


@alt_access_key_required
@alt_admin_required
def alt_investment_edit(request, pk):
    item = get_object_or_404(AlternativeInvestmentItem, pk=pk)
    if request.method == "POST":
        form = AlternativeInvestmentItemForm(request.POST, instance=item)
        if form.is_valid():
            details = build_change_details(form)
            form.save()
            event_type = "status_changed" if "status" in form.changed_data else "updated"
            log_dashboard_event(
                dashboard_key="alternative_investments",
                event_type=event_type,
                section_label="Investment Reviews",
                record_label=item.investment_name,
                summary=f"Updated investment review for {item.investment_name}.",
                details=details,
                actor_label=actor_label(request, "Alternative Investments Admin"),
            )
            messages.success(request, f"Updated {item.investment_name}.")
            return redirect("alt_investments_reviews")
    else:
        form = AlternativeInvestmentItemForm(instance=item)

    return render(
        request,
        "reports/alt_investment_form.html",
        {
            "form": form,
            "item": item,
            "is_alt_admin": True,
            "hide_global_nav": True,
        },
    )


@alt_access_key_required
@alt_admin_required
def alt_investment_add(request):
    """Create a new alternative investment."""
    if request.method == "POST":
        form = AlternativeInvestmentItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            log_dashboard_event(
                dashboard_key="alternative_investments",
                event_type="created",
                section_label="Investment Reviews",
                record_label=item.investment_name,
                summary=f"Added alternative investment: {item.investment_name}.",
                details=f"Status: {item.get_status_display()}",
                actor_label=actor_label(request, "Alternative Investments Admin"),
            )
            messages.success(request, f"Created {item.investment_name}.")
            return redirect("alt_investment_detail", pk=item.pk)
    else:
        form = AlternativeInvestmentItemForm()

    return render(
        request,
        "reports/alt_investment_form.html",
        {
            "form": form,
            "item": None,
            "is_alt_admin": True,
            "hide_global_nav": True,
        },
    )


@alt_access_key_required
@alt_admin_required
def alt_investment_delete(request, pk):
    """Delete an alternative investment with confirmation."""
    item = get_object_or_404(AlternativeInvestmentItem, pk=pk)
    if request.method == "POST":
        investment_name = item.investment_name
        item.delete()
        log_dashboard_event(
            dashboard_key="alternative_investments",
            event_type="deleted",
            section_label="Investment Reviews",
            record_label=investment_name,
            summary=f"Deleted alternative investment: {investment_name}.",
            details="Alternative investment record removed.",
            actor_label=actor_label(request, "Alternative Investments Admin"),
        )
        messages.success(request, f"Deleted {investment_name}.")
        return redirect("alt_investments_reviews")

    return render(
        request,
        "reports/alt_investment_delete_confirm.html",
        {
            "item": item,
            "hide_global_nav": True,
        },
    )
def hr_action_items_dashboard(request):
    return render(
        request,
        "reports/dashboard_placeholder.html",
        {
            "title": "HR Action Items Dashboard",
            "description": "This dashboard module is reserved for HR action items, ownership tracking, and completion workflow.",
        },
    )
