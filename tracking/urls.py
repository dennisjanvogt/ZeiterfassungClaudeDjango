from django.urls import path
from tracking.views import (
    # Dashboard
    dashboard,

    # Client
    client_list, client_detail, delete_client,

    # Project
    project_list, project_detail, delete_project,

    # Time Entry
    time_entry, stop_timer, edit_time_entry, delete_time_entry,

    # Analytics
    analytics,

    # Auth
    register_view, custom_login_view,

    # Profile
    profile_view, edit_profile, change_password,

    # Export
    export_report,
)
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Dashboard
    path('', dashboard, name='dashboard'),

    # Client
    path('clients/', client_list, name='client_list'),
    path('clients/<int:client_id>/', client_detail, name='client_detail'),
    path('clients/<int:client_id>/delete/',
         delete_client, name='delete_client'),

    # Project
    path('projects/', project_list, name='project_list'),
    path('projects/<int:project_id>/', project_detail, name='project_detail'),
    path('projects/<int:project_id>/delete/',
         delete_project, name='delete_project'),

    # Time Entry
    path('time-entry/', time_entry, name='time_entry'),
    path('time-entry/stop/<int:entry_id>/', stop_timer, name='stop_timer'),
    path('time-entry/edit/<int:entry_id>/',
         edit_time_entry, name='edit_time_entry'),
    path('time-entry/delete/<int:entry_id>/',
         delete_time_entry, name='delete_time_entry'),

    # Analytics
    path('analytics/', analytics, name='analytics'),

    # Auth
    path('register/', register_view, name='register'),
    path('login/', custom_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Profile
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('profile/change-password/', change_password, name='change_password'),

    # Export
    path('export/', export_report, name='export_report'),
]
