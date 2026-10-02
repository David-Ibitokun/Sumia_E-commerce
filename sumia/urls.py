"""
URL configuration for sumia project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    path('', include('shop.urls')),
    path('', include('authentications.urls')),
]

# Error pages served for unhandled exceptions and unknown URLs.
handler404 = 'pages.views.public.page404'
handler500 = 'pages.views.public.page500'
handler503 = 'pages.views.public.page503'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
