"""Routes for authentication, registration and the role dashboards."""
from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),

    # Dashboards
    path('dashboard/user/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/vendor/', views.vendor_dashboard, name='vendor_dashboard'),

    # Profile
    path('myProfile/', views.my_profile, name='my_profile'),
]
