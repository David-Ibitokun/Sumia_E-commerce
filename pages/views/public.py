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


def health_check(request):
    """Health check endpoint to verify web application and database connectivity."""
    from django.db import connection
    from django.http import JsonResponse
    import time

    status_data = {
        'status': 'healthy',
        'timestamp': int(time.time()),
        'database': 'unknown',
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        status_data['database'] = 'connected'
        return JsonResponse(status_data, status=200)
    except Exception as e:
        status_data['status'] = 'unhealthy'
        status_data['database'] = f'error: {str(e)}'
        return JsonResponse(status_data, status=503)
