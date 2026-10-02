"""Routes for the pages app."""
from django.urls import path

from .views import account, public

urlpatterns = [
    path('', public.home, name='home'),
    path('about/', public.about, name='about'),
    path('contact/', public.contact, name='contact'),
    path('my-account/', account.my_account, name='my_account'),
    path('myAccount/', account.my_account, name='myAccount'),  # legacy alias

    # Error pages, also reachable as the project wide handlers in sumia.urls.
    path('page404/', public.page404, name='page404'),
    path('page500/', public.page500, name='page500'),
    path('page503/', public.page503, name='page503'),
]
