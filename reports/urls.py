from django.urls import path

from . import views

urlpatterns = [
    path("unlock/", views.unlock_access, name="unlock_access"),
    path("exit/", views.exit_access, name="exit_access"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("tracker/", views.report_tracker, name="report_tracker"),
    path("operations/", views.operations_staff_view, name="operations_staff"),
    path("reports/<int:pk>/edit/", views.edit_report, name="report_edit"),
]
