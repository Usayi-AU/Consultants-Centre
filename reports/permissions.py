from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

TEAM_ACCESS_KEY = "01"
ADMIN_ACCESS_KEY = "int@operationsADMIN"
CRM_TEAM_ACCESS_KEY = "02"
CRM_ADMIN_ACCESS_KEY = "crmsadmin"
ALT_TEAM_ACCESS_KEY = "03"
ALT_ADMIN_ACCESS_KEY = "20"
BD_TEAM_ACCESS_KEY = "04"
BD_ADMIN_ACCESS_KEY = "Shongz"


def access_level(request):
    return request.session.get("access_level")


def is_ops_admin(request):
    return access_level(request) == "admin"


def expected_access_key(request):
    return ADMIN_ACCESS_KEY if is_ops_admin(request) else TEAM_ACCESS_KEY


def access_key_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.session.get("access_key") != expected_access_key(request):
            messages.info(request, "Enter your team passkey to unlock dashboard access.")
            return redirect("unlock_access")
        return view_func(request, *args, **kwargs)

    return _wrapped


def ops_team_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.session.get("access_level") not in {"team", "admin"}:
            messages.info(request, "Enter the team passkey to continue.")
            return redirect("unlock_access")
        return view_func(request, *args, **kwargs)

    return _wrapped


def ops_admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.session.get("access_level") != "admin":
            messages.info(request, "Enter the admin passkey to access this page.")
            return redirect("unlock_access")
        return view_func(request, *args, **kwargs)

    return _wrapped


def crm_access_level(request):
    return request.session.get("crm_access_level")


def is_crm_admin(request):
    return crm_access_level(request) == "admin"


def expected_crm_access_key(request):
    return CRM_ADMIN_ACCESS_KEY if is_crm_admin(request) else CRM_TEAM_ACCESS_KEY


def crm_access_key_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.session.get("crm_access_key") != expected_crm_access_key(request):
            messages.info(request, "Enter your Client Relations passkey to continue.")
            return redirect("crm:unlock_access")
        return view_func(request, *args, **kwargs)

    return _wrapped


def crm_admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.session.get("crm_access_level") != "admin":
            messages.info(request, "Admin CRM passkey is required for that action.")
            return redirect("crm_dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped


def alt_access_level(request):
    return request.session.get("alt_access_level")


def is_alt_admin(request):
    return alt_access_level(request) == "admin"


def expected_alt_access_key(request):
    return ALT_ADMIN_ACCESS_KEY if is_alt_admin(request) else ALT_TEAM_ACCESS_KEY


def alt_access_key_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.session.get("alt_access_key") != expected_alt_access_key(request):
            messages.info(request, "Enter your Alternative Investments passkey to continue.")
            return redirect("alt_investments_unlock")
        return view_func(request, *args, **kwargs)

    return _wrapped


def alt_admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.session.get("alt_access_level") != "admin":
            messages.info(request, "Admin Alternative Investments passkey is required for that action.")
            return redirect("alt_investments_dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped


def bd_access_level(request):
    return request.session.get("bd_access_level")


def is_bd_admin(request):
    return bd_access_level(request) == "admin"


def expected_bd_access_key(request):
    return BD_ADMIN_ACCESS_KEY if is_bd_admin(request) else BD_TEAM_ACCESS_KEY


def bd_access_key_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.session.get("bd_access_key") != expected_bd_access_key(request):
            messages.info(request, "Enter your Business Development passkey to continue.")
            return redirect("business_development_unlock")
        return view_func(request, *args, **kwargs)

    return _wrapped


def bd_admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.session.get("bd_access_level") != "admin":
            messages.info(request, "Admin Business Development passkey is required for that action.")
            return redirect("business_development_dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped
