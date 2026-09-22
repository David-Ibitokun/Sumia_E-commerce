from django.urls import path
from .views import (
    home, about, contact, page404, page500, page503,
    login, register, myAccount, password_change_done,
)

urlpatterns = [
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('page404/', page404, name='page404'),
    path('page500/', page500, name='page500'),
    path('page503/', page503, name='page503'),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('myAccount/', myAccount, name='myAccount'),
    path('password-change-done/', password_change_done, name='password_change_done'),
]
