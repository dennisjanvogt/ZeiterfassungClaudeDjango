# Import all views to make them available at the package level
from tracking.views.dashboard import dashboard
from tracking.views.client import client_list, client_detail, delete_client
from tracking.views.project import project_list, project_detail, delete_project
from tracking.views.time_entry import time_entry, stop_timer, edit_time_entry, delete_time_entry
from tracking.views.analytics import analytics
from tracking.views.auth import register_view, custom_login_view
from tracking.views.profile import profile_view, edit_profile, change_password
from tracking.views.export import export_report

# This allows you to import directly from tracking.views
__all__ = [
    'dashboard',
    'client_list', 'client_detail', 'delete_client',
    'project_list', 'project_detail', 'delete_project',
    'time_entry', 'stop_timer', 'edit_time_entry', 'delete_time_entry',
    'analytics',
    'register_view', 'custom_login_view',
    'profile_view', 'edit_profile', 'change_password',
    'export_report',
]
