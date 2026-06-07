from django.urls import path

from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('unlock/', views.unlock_access, name='unlock_access'),
    path('exit/', views.exit_dashboard, name='exit_dashboard'),
    path('action-items/', views.client_action_items, name='client_action_items'),
    path('action-item/new/', views.create_action_item, name='create_action_item'),
    path('client-hub/', views.client_hub, name='client_hub'),
    path('client/<str:client_name>/', views.client_detail, name='client_detail'),
    path('action-item/<int:pk>/edit/', views.edit_action_item, name='edit_action_item'),
    path('action-item/<int:pk>/delete/', views.delete_action_item, name='delete_action_item'),
    path('admin-activity/', views.admin_activity, name='admin_activity'),
    path('history/<int:pk>/delete/', views.delete_history, name='delete_history'),
]
