from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from tracking.views import custom_login_view, register_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', custom_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        http_method_names=['get', 'post']), name='logout'),
    path('register/', register_view, name='register'),
    # Stellt sicher, dass alle URLs aus tracking.urls eingebunden sind
    path('', include('tracking.urls')),
]
