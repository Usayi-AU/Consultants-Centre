from collections import defaultdict

from .models import ClientReport, StatusPhase


def percent(done, total):
    if not total:
        return 0
    return round((done / total) * 100, 1)


def build_summary():
    reports = ClientReport.objects.all()
    total = reports.count()
    submitted = reports.filter(status_phase=StatusPhase.SUBMITTED).count()
    reviewed = reports.filter(status_phase=StatusPhase.REVIEWED).count()
    sent = reports.filter(status_phase=StatusPhase.SENT_TO_CLIENT).count()
    return {
        "total_clients": total,
        "submitted_count": submitted,
        "reviewed_count": reviewed,
        "sent_count": sent,
        "outstanding_count": total - sent,
        "completion_rate": percent(sent, total),
    }


def build_grouped_progress(group_field):
    rows = []
    groups = defaultdict(list)
    for report in ClientReport.objects.all().order_by(group_field, "client_name"):
        groups[getattr(report, group_field)].append(report)

    for group_name, reports in groups.items():
        total = len(reports)
        submitted = sum(1 for report in reports if report.status_phase == StatusPhase.SUBMITTED)
        reviewed = sum(1 for report in reports if report.status_phase == StatusPhase.REVIEWED)
        sent = sum(1 for report in reports if report.status_phase == StatusPhase.SENT_TO_CLIENT)
        rows.append(
            {
                "name": group_name,
                "total": total,
                "submitted": submitted,
                "reviewed": reviewed,
                "sent": sent,
                "percent_done": percent(sent, total),
                "reports": reports,
            }
        )
    return rows


def status_badge_class(phase):
    return {
        StatusPhase.PENDING: "bg-slate-100 text-slate-700 ring-slate-200",
        StatusPhase.SUBMITTED: "bg-amber-100 text-amber-800 ring-amber-200",
        StatusPhase.REVIEWED: "bg-sky-100 text-sky-800 ring-sky-200",
        StatusPhase.SENT_TO_CLIENT: "bg-emerald-100 text-emerald-800 ring-emerald-200",
    }.get(phase, "bg-slate-100 text-slate-700 ring-slate-200")
