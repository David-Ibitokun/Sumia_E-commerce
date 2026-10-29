"""Public, read-only pages: home, static pages and error pages.

Authentication lives in the `authentications` app; account specific pages that
are not part of that flow live in `account.py`.
"""
import os
import time
from django.shortcuts import render
from django.db import connection
from django.core.cache import cache
from django.http import JsonResponse

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
    """Health check endpoint to verify web application, database, and cache connectivity."""
    status_data = {
        'status': 'healthy',
        'timestamp': int(time.time()),
        'database': 'unknown',
        'cache': 'unknown',
    }
    is_healthy = True

    # 1. Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        status_data['database'] = 'connected'
    except Exception as e:
        status_data['database'] = f'error: {str(e)}'
        is_healthy = False

    # 2. Cache check
    try:
        cache.set('__health__', 'ok', timeout=10)
        cached_val = cache.get('__health__')
        if cached_val == 'ok':
            status_data['cache'] = 'connected'
        else:
            status_data['cache'] = 'degraded'
    except Exception as e:
        status_data['cache'] = f'error: {str(e)}'
        # In development without Redis, cache failure is non-fatal unless in production
        if os.environ.get('REDIS_URL'):
            is_healthy = False

    status_data['status'] = 'healthy' if is_healthy else 'unhealthy'
    status_code = 200 if is_healthy else 503
    return JsonResponse(status_data, status=status_code)
