"""Order placement and order queries.

Stock is decremented, prices are snapshotted and the cart is emptied inside a
single transaction so a failure cannot leave a half placed order behind.
"""
import logging

from django.db import transaction
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404

from pages.models import CartItem, Order, OrderItem, Product

from .exceptions import InsufficientStockError

#: Methods where the shopper pays after delivery, so the order starts unpaid.
UNPAID_METHODS = {Order.PAYMENT_METHOD_COD}

ORDER_LOOKUPS = ('user',)
ORDER_PREFETCH_LOOKUPS = ('orderitem_set__product',)

logger = logging.getLogger(__name__)


def create_order(user, cart, shipping_data):
    """Turn a cart into an order.

    ``shipping_data`` holds the validated checkout fields (address, city,
    zip_code, country, phone_number, payment_method).
    """
    payment_method = shipping_data.get('payment_method')

    try:
        with transaction.atomic():
            items = list(
                CartItem.objects.filter(cart=cart)
                .select_related('product')
                .select_for_update(of=('product',))
                .order_by('product_id')
            )
            if not items:
                raise InsufficientStockError("Your cart is empty.")

            # Aggregate quantities for the same product to avoid double-decrement
            aggregated = {}
            for item in items:
                pid = item.product_id
                if pid in aggregated:
                    aggregated[pid]['quantity'] += item.quantity
                else:
                    aggregated[pid] = {
                        'product': item.product,
                        'quantity': item.quantity,
                        'price': item.product.get_display_price(),
                    }

            total_price = sum(
                data['quantity'] * data['price'] for data in aggregated.values()
            )
            _reserve_stock(aggregated)

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
                        product_id=pid,
                        quantity=data['quantity'],
                        price_at_purchase=data['price'],
                    )
                    for pid, data in aggregated.items()
                ]
            )

            CartItem.objects.filter(cart=cart).delete()
            cart.delete()

        return order

    except InsufficientStockError:
        raise
    except Exception as exc:
        logger.exception("Order creation failed for user %s: %s", user.id, exc)
        raise InsufficientStockError("Unable to process your order. Please try again.") from exc


def _reserve_stock(aggregated):
    """Lock and decrement the stock of every purchased product.

    Uses a single bulk update for all products to minimize database round-trips
    and avoid per-item save() calls inside the transaction.
    """
    product_ids = list(aggregated.keys())
    products = Product.objects.filter(pk__in=product_ids).select_for_update()

    product_map = {p.pk: p for p in products}
    to_update = []

    for pid, data in aggregated.items():
        product = product_map.get(pid)
        if product is None:
            logger.error("Cart item references deleted product %s", pid)
            raise InsufficientStockError("One of the products in your cart is no longer available.")

        qty = data['quantity']
        if qty > product.stock_quantity:
            logger.warning(
                "Insufficient stock for product %s (requested: %s, available: %s)",
                product.name,
                qty,
                product.stock_quantity,
            )
            raise InsufficientStockError(f"Not enough stock for {product.name}.")

        product.stock_quantity -= qty
        to_update.append(product)

    if to_update:
        Product.objects.bulk_update(to_update, ['stock_quantity'])


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