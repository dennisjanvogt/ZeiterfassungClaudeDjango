from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from tracking.views import (
    custom_login_view, 
    register_view
)

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Authentication paths
    path('login/', custom_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='login',
        http_method_names=['get', 'post']
    ), name='logout'),
    path('register/', register_view, name='register'),
    
    # Include tracking app URLs
    path('', include('tracking.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)