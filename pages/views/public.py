"""Public, read-only pages: home, static pages and error pages.

Authentication lives in the `authentications` app; account specific pages that
are not part of that flow live in `account.py`.
"""
from django.shortcuts import render

from shop.services import catalog

FEATURED_PRODUCT_LIMIT = 12


def home(request):
    """Landing page with the newest products."""
    return render(
        request,
        'pages/index.html',
        {'products': catalog.latest_products(FEATURED_PRODUCT_LIMIT)},
    )


def about(request):
    return render(request, 'pages/about.html')


def contact(request):
    return render(request, 'pages/contact.html')


def page404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def page500(request):
    return render(request, 'errors/500.html', status=500)


def page503(request):
    return render(request, 'errors/503.html', status=503)
