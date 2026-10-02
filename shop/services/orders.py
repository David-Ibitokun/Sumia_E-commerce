"""Order placement and order queries.

Stock is decremented, prices are snapshotted and the cart is emptied inside a
single transaction so a failure cannot leave a half placed order behind.
"""
from django.db import transaction
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404

from pages.models import CartItem, Order, OrderItem, Product

from .exceptions import InsufficientStockError

#: Methods where the shopper pays after delivery, so the order starts unpaid.
UNPAID_METHODS = {Order.PAYMENT_METHOD_COD}

ORDER_LOOKUPS = ('user',)
ORDER_PREFETCH_LOOKUPS = ('orderitem_set__product',)


def create_order(user, cart, shipping_data):
    """Turn a cart into an order.

    ``shipping_data`` holds the validated checkout fields (address, city,
    zip_code, country, phone_number, payment_method).
    """
    items = list(CartItem.objects.filter(cart=cart).select_related('product'))
    if not items:
        raise InsufficientStockError("Your cart is empty.")

    payment_method = shipping_data.get('payment_method')
    total_price = sum(item.get_total_price() for item in items)

    with transaction.atomic():
        _reserve_stock(items)

        order = Order.objects.create(
            user=user,
            total_price=total_price,
            is_paid=payment_method not in UNPAID_METHODS,
            **shipping_data,
        )

        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_at_purchase=item.product.get_display_price(),
                )
                for item in items
            ]
        )

        CartItem.objects.filter(cart=cart).delete()
        cart.delete()

    return order


def _reserve_stock(items):
    """Lock and decrement the stock of every purchased product."""
    for item in items:
        product = Product.objects.select_for_update().get(pk=item.product_id)
        if item.quantity > product.stock_quantity:
            raise InsufficientStockError(f"Not enough stock for {product.name}.")
        product.stock_quantity -= item.quantity
        product.save(update_fields=['stock_quantity'])


def orders_for_user(user):
    """A user's orders, newest first."""
    return Order.objects.filter(user=user).select_related(*ORDER_LOOKUPS)


def get_user_order(user, order_number):
    """Fetch one of the user's own orders, or raise 404."""
    return get_object_or_404(
        Order.objects.prefetch_related(*ORDER_PREFETCH_LOOKUPS),
        order_number=order_number,
        user=user,
    )


def order_items(order):
    """Order lines with their products prefetched."""
    return order.orderitem_set.select_related('product')


def vendor_line_filter(vendor):
    """Q matching the order lines a vendor actually sold."""
    return Q(orderitem__product__creator=vendor)


def orders_for_vendor(vendor):
    """Orders containing at least one of the vendor's products, newest first.

    Each order is annotated with ``vendor_total_amount``: the revenue from the
    vendor's own lines, which is not the order total when other vendors sold
    into the same order.
    """
    vendor_items = vendor_line_filter(vendor)
    return (
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


def get_vendor_order(vendor, order_number):
    """Fetch one order the vendor has a line in, or raise 404.

    Ownership is part of the lookup, so an order the vendor sold nothing into
    is indistinguishable from one that does not exist.
    """
    return get_object_or_404(
        orders_for_vendor(vendor), order_number=order_number
    )


def vendor_order_items(vendor, order):
    """The vendor's own lines of one order."""
    return (
        OrderItem.objects.filter(order=order, product__creator=vendor)
        .select_related('product')
    )
