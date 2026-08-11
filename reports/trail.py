from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from crm.models import ActionItemHistory

from .models import DashboardTrailEvent


TRAIL_LOOKBACK_DAYS = 180
TRAIL_MAX_ITEMS = 150


class DashboardContext:
    def __init__(self, key="", label="", enabled=False):
        self.key = key
        self.label = label
        self.enabled = enabled


def resolve_dashboard_context(request):
    path = request.path or ""

    if path.startswith("/crm/"):
        return DashboardContext(
            key=DashboardTrailEvent.DashboardKey.CLIENT_RELATIONS,
            label="Client Relations Dashboard",
            enabled=bool(request.session.get("crm_access")),
        )

    if path.startswith("/dashboards/business-development/"):
        return DashboardContext(
            key=DashboardTrailEvent.DashboardKey.BUSINESS_DEVELOPMENT,
            label="Business Development Dashboard",
            enabled=bool(request.session.get("bd_access_key")),
        )

    if path.startswith("/dashboards/alternative-investments/"):
        return DashboardContext(
            key=DashboardTrailEvent.DashboardKey.ALTERNATIVE_INVESTMENTS,
            label="Alternative Investments Dashboard",
            enabled=bool(request.session.get("alt_access_key")),
        )

    ops_prefixes = (
        "/dashboard",
        "/tracker/",
        "/sharepoint-tracker/",
        "/operations/",
        "/reports/",
    )
    if path == "/dashboard" or any(path.startswith(prefix) for prefix in ops_prefixes):
        return DashboardContext(
            key=DashboardTrailEvent.DashboardKey.OPERATIONS,
            label="Operations Dashboard",
            enabled=bool(request.session.get("access_key")),
        )

    return DashboardContext()


def _format_value(value):
    if value is None or value == "":
        return "-"
    if hasattr(value, "strftime"):
        return value.strftime("%d %b %Y")
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def build_change_details(form, field_labels=None, max_fields=6):
    field_labels = field_labels or {}
    if not getattr(form, "changed_data", None):
        return ""

    lines = []
    for field in form.changed_data[:max_fields]:
        label = field_labels.get(field, field.replace("_", " ").title())
        old_value = _format_value(form.initial.get(field))
        new_value = _format_value(form.cleaned_data.get(field))
        lines.append(f"{label}: {old_value} -> {new_value}")

    extra_count = len(form.changed_data) - max_fields
    if extra_count > 0:
        lines.append(f"+ {extra_count} more field(s) updated")

    return "; ".join(lines)


def log_dashboard_event(
    *,
    dashboard_key,
    event_type,
    summary,
    section_label="",
    record_label="",
    details="",
    actor_label="Admin",
    metadata=None,
):
    DashboardTrailEvent.objects.create(
        dashboard_key=dashboard_key,
        event_type=event_type,
        section_label=section_label,
        record_label=record_label,
        summary=summary,
        details=details,
        actor_label=actor_label or "Admin",
        metadata=metadata or {},
    )


def parse_actor_from_crm_change(change_text):
    if " by " not in change_text:
        return "Admin"
    token = change_text.split(" by ", 1)[1].split("\u2022", 1)[0].strip()
    return token or "Admin"


def _crm_entries(cutoff):
    entries = []

    history_rows = ActionItemHistory.objects.select_related("action_item").filter(timestamp__gte=cutoff).order_by("-timestamp")[:TRAIL_MAX_ITEMS]
    for row in history_rows:
        if not row.action_item_id:
            continue
        entries.append(
            {
                "summary": row.changes.split("\u2022", 1)[0].strip() or "CRM update recorded.",
                "details": row.changes,
                "section": "Action Items",
                "record": row.action_item.client,
                "actor": parse_actor_from_crm_change(row.changes),
                "timestamp": row.timestamp,
            }
        )

    delete_rows = DashboardTrailEvent.objects.filter(
        dashboard_key=DashboardTrailEvent.DashboardKey.CLIENT_RELATIONS,
        event_type=DashboardTrailEvent.EventType.DELETED,
        created_at__gte=cutoff,
    ).order_by("-created_at")[:TRAIL_MAX_ITEMS]

    for row in delete_rows:
        entries.append(
            {
                "summary": row.summary,
                "details": row.details,
                "section": row.section_label,
                "record": row.record_label,
                "actor": row.actor_label,
                "timestamp": row.created_at,
            }
        )

    entries.sort(key=lambda item: item["timestamp"], reverse=True)
    return entries[:TRAIL_MAX_ITEMS]


def _dashboard_entries(dashboard_key, cutoff):
    queryset = DashboardTrailEvent.objects.filter(dashboard_key=dashboard_key, created_at__gte=cutoff).order_by("-created_at")[:TRAIL_MAX_ITEMS]
    entries = []
    for row in queryset:
        entries.append(
            {
                "summary": row.summary,
                "details": row.details,
                "section": row.section_label,
                "record": row.record_label,
                "actor": row.actor_label,
                "timestamp": row.created_at,
            }
        )
    return entries


def build_trail_timeline(request):
    dashboard_context = resolve_dashboard_context(request)
    if not dashboard_context.enabled or not dashboard_context.key:
        return dashboard_context, []

    cutoff = timezone.now() - timedelta(days=TRAIL_LOOKBACK_DAYS)
    if dashboard_context.key == DashboardTrailEvent.DashboardKey.CLIENT_RELATIONS:
        entries = _crm_entries(cutoff)
    else:
        entries = _dashboard_entries(dashboard_context.key, cutoff)

    local_today = timezone.localdate()
    grouped = defaultdict(list)

    for entry in entries:
        local_dt = timezone.localtime(entry["timestamp"])
        grouped[local_dt.date()].append(
            {
                "summary": entry["summary"],
                "details": entry["details"],
                "section": entry["section"],
                "record": entry["record"],
                "actor": entry["actor"],
                "datetime_label": local_dt.strftime("%d %b %Y %H:%M"),
                "time_label": local_dt.strftime("%H:%M"),
            }
        )

    timeline = []
    for date_value in sorted(grouped.keys(), reverse=True):
        if date_value == local_today:
            label = f"Today - {date_value.strftime('%d %B %Y')}"
        elif date_value == (local_today - timedelta(days=1)):
            label = f"Yesterday - {date_value.strftime('%d %B %Y')}"
        else:
            label = date_value.strftime("%A - %d %B %Y")

        timeline.append(
            {
                "date": date_value,
                "label": label,
                "entries": grouped[date_value],
            }
        )

    return dashboard_context, timeline
