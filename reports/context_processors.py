from .trail import build_trail_timeline


def dashboard_trail_context(request):
    dashboard_context, timeline = build_trail_timeline(request)
    return {
        "trail_enabled": dashboard_context.enabled,
        "trail_dashboard_key": dashboard_context.key,
        "trail_dashboard_label": dashboard_context.label,
        "trail_timeline": timeline,
        "trail_entry_count": sum(len(group["entries"]) for group in timeline),
    }
