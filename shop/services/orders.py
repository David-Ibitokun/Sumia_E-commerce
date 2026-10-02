"""Order placement and order queries.

Stock is decremented, prices are snapshotted and the cart is emptied inside a
single transaction so a failure cannot leave a half placed order behind.
"""
from django.db import transaction
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
