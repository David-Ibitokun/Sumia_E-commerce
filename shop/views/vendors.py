"""Order views scoped to the products a vendor created.

Vendors never see the whole order: only their own lines and the revenue those
lines represent. `vendor_order_detail` additionally refuses orders the vendor
has no line in, so an order number cannot be used to probe unrelated sales.
"""
from django.shortcuts import render

from pages.decorators import vendor_required

from shop.services import orders as order_service


@vendor_required
def vendor_orders(request):
    """Orders that contain at least one of the vendor's products."""
    return render(
        request,
        'vendor/orders.html',
        {'orders': order_service.orders_for_vendor(request.user)},
    )


@vendor_required
def vendor_order_detail(request, order_number):
    """The vendor's own lines of one order, plus their subtotal."""
    order = order_service.get_vendor_order(request.user, order_number)
    order_items = order_service.vendor_order_items(request.user, order)

    return render(
        request,
        'vendor/order_detail.html',
        {
            'order': order,
            'vendor_order_items': order_items,
            'vendor_total_price': sum(item.get_total_price() for item in order_items),
        },
    )
