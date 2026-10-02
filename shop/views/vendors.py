"""Order views scoped to the products a vendor created.

Vendors never see the whole order: only their own lines and the revenue those
lines represent.
"""
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404, render

from pages.models import Order, OrderItem


@login_required(login_url='login')
def vendor_orders(request):
    """Orders that contain at least one of the vendor's products."""
    vendor_items = Q(orderitem__product__creator=request.user)
    orders = (
        Order.objects.filter(vendor_items)
        .distinct()
        .select_related('user')
        .prefetch_related('orderitem_set__product')
        .annotate(
            vendor_total_amount=Sum(
                F('orderitem__quantity') * F('orderitem__price_at_purchase'),
                filter=vendor_items,
            )
        )
        .order_by('-created_at')
    )
    return render(request, 'vendor/orders.html', {'orders': orders})


@login_required(login_url='login')
def vendor_order_detail(request, order_number):
    """The vendor's own lines of one order, plus their subtotal."""
    order = get_object_or_404(
        Order.objects.select_related('user'), order_number=order_number
    )
    order_items = (
        OrderItem.objects.filter(order=order, product__creator=request.user)
        .select_related('product')
    )

    return render(
        request,
        'vendor/order_detail.html',
        {
            'order': order,
            'vendor_order_items': order_items,
            'vendor_total_price': sum(item.get_total_price() for item in order_items),
        },
    )
