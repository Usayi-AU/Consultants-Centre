from django.urls import path

from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('unlock/', views.unlock_access, name='unlock_access'),
    path('meetings/unlock/', views.meetings_unlock, name='meetings_unlock'),
    path('exit/', views.exit_dashboard, name='exit_dashboard'),
    path('action-items/', views.client_action_items, name='client_action_items'),
    path('action-item/new/', views.create_action_item, name='create_action_item'),
    path('client-hub/', views.client_hub, name='client_hub'),
    path('client/<str:client_name>/', views.client_detail, name='client_detail'),
    path('action-item/<int:pk>/edit/', views.edit_action_item, name='edit_action_item'),
    path('action-item/<int:pk>/delete/', views.delete_action_item, name='delete_action_item'),
    path('admin-activity/', views.admin_activity, name='admin_activity'),
    path('history/<int:pk>/delete/', views.delete_history, name='delete_history'),
    path('meetings/', views.meetings_list, name='meetings_list'),
    path('meetings/new/', views.create_meeting, name='create_meeting'),
    path('meetings/<int:pk>/', views.meeting_detail, name='meeting_detail'),
    path('meetings/<int:meeting_pk>/action/<int:pk>/edit/', views.edit_meeting_action_point, name='edit_meeting_action_point'),
    path('meetings/<int:pk>/delete/', views.delete_meeting, name='delete_meeting'),
]
