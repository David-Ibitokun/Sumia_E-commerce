"""Aggregates behind the two role dashboards.

Each function returns a plain dict so a template can read named figures without
knowing how they were counted. Every query is scoped to the signed in account,
so a dashboard can never surface another account's rows.
"""
from django.db.models import F, Sum

from pages.models import Order, OrderItem, Product

from . import cart as cart_service
from . import orders as order_service
from . import wishlist as wishlist_service

#: Stock at or below this is surfaced as "running low" on the vendor dashboard.
LOW_STOCK_THRESHOLD = 5

#: How many rows the "recent activity" lists show.
RECENT_LIMIT = 5

#: Cancelled orders are excluded from spend and revenue figures.
COUNTED_STATUSES = [
    status for status, _ in Order.STATUS_CHOICES if status != 'cancelled'
]

PRODUCT_FIELDS = ('category', 'brand')


def _vendor_items(vendor):
    """Order lines belonging to ``vendor``, excluding cancelled orders."""
    return OrderItem.objects.filter(
        product__creator=vendor, order__status__in=COUNTED_STATUSES
    )


def vendor_stats(vendor):
    """Headline figures and recent activity for a vendor dashboard."""
    products = Product.objects.filter(creator=vendor)
    items = _vendor_items(vendor)
    totals = items.aggregate(
        units_sold=Sum('quantity'),
        revenue=Sum(F('quantity') * F('price_at_purchase')),
    )

    return {
        'product_count': products.count(),
        'live_product_count': products.filter(is_available=True).count(),
        'low_stock_count': products.filter(
            is_available=True, stock_quantity__lte=LOW_STOCK_THRESHOLD
        ).count(),
        'low_stock_threshold': LOW_STOCK_THRESHOLD,
        'order_count': order_service.orders_for_vendor(vendor).count(),
        'units_sold': totals['units_sold'] or 0,
        'revenue': totals['revenue'] or 0,
        'recent_orders': order_service.orders_for_vendor(vendor)[:RECENT_LIMIT],
        'recent_products': (
            products.select_related(*PRODUCT_FIELDS).order_by('-created_at')[
                :RECENT_LIMIT
            ]
        ),
    }


def customer_stats(user):
    """Headline figures and recent activity for a shopper dashboard."""
    orders = order_service.orders_for_user(user)
    spend = orders.filter(status__in=COUNTED_STATUSES).aggregate(
        total=Sum('total_price')
    )

    return {
        'order_count': orders.count(),
        'total_spent': spend['total'] or 0,
        'cart_count': cart_service.item_count(user),
        'wishlist_count': wishlist_service.count_for_user(user),
        'recent_orders': orders[:RECENT_LIMIT],
    }
