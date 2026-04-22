from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReportStatusForm
from .models import ClientReport
from .permissions import ADMIN_ACCESS_KEY, TEAM_ACCESS_KEY, access_key_required, is_ops_admin, ops_admin_required
from .utils import build_grouped_progress, build_summary, status_badge_class


def unlock_access(request):
    if request.method == "POST":
        passkey = request.POST.get("passkey", "")
        if passkey == ADMIN_ACCESS_KEY:
            request.session["access_key"] = ADMIN_ACCESS_KEY
            request.session["access_level"] = "admin"
            messages.success(request, "Admin passkey accepted. Dashboard unlocked.")
            return redirect("dashboard")
        if passkey == TEAM_ACCESS_KEY:
            request.session["access_key"] = TEAM_ACCESS_KEY
            request.session["access_level"] = "team"
            messages.success(request, "Team passkey accepted. Dashboard unlocked.")
            return redirect("dashboard")
        messages.error(request, "Invalid passkey.")

    current_level = request.session.get("access_level")
    return render(
        request,
        "reports/unlock_access.html",
        {
            "is_ops_admin": current_level == "admin",
        },
    )


def exit_access(request):
    request.session.flush()
    messages.success(request, "Session cleared. You have exited the dashboard.")
    return redirect("unlock_access")


@access_key_required
def dashboard(request):
    search_query = request.GET.get("q", "").strip()
    reports = ClientReport.objects.all()
    if search_query:
        reports = reports.filter(
            Q(client_name__icontains=search_query)
            | Q(crm_name__icontains=search_query)
            | Q(operations_assignee__icontains=search_query)
        )

    summary = build_summary()
    crm_rows = build_grouped_progress("crm_name")
    operations_rows = build_grouped_progress("operations_assignee")
    chart_data = {
        "summary": {
            "pending": summary["total_clients"] - summary["submitted_count"],
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
        },
    )


@access_key_required
def report_tracker(request):
    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    reports = ClientReport.objects.all()
    if search_query:
        reports = reports.filter(
            Q(client_name__icontains=search_query)
            | Q(crm_name__icontains=search_query)
            | Q(operations_assignee__icontains=search_query)
        )
    if status_filter:
        reports = reports.filter(status_phase=status_filter)

    return render(
        request,
        "reports/report_tracker.html",
        {
            "reports": reports,
            "search_query": search_query,
            "status_filter": status_filter,
            "status_badge_class": status_badge_class,
            "show_edit_actions": is_ops_admin(request),
        },
    )


@ops_admin_required
@access_key_required
def operations_staff_view(request):
    return render(
        request,
        "reports/operations_staff.html",
        {
            "operations_rows": build_grouped_progress("operations_assignee"),
            "status_badge_class": status_badge_class,
        },
    )


@ops_admin_required
@access_key_required
def edit_report(request, pk):
    report = get_object_or_404(ClientReport, pk=pk)
    if request.method == "POST":
        form = ReportStatusForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated {report.client_name}.")
            return redirect("report_tracker")
    else:
        form = ReportStatusForm(instance=report)

    return render(request, "reports/report_form.html", {"form": form, "report": report})
