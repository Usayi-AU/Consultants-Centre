from .views import get_crm_access


def crm_access_state(request):
    return {"access_state": get_crm_access(request)}
