from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

TEAM_ACCESS_KEY = "operations@int"
ADMIN_ACCESS_KEY = "int@operationsADMIN"


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
