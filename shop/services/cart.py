"""Cart mutations and totals.

Both the regular and the AJAX cart views go through this module so stock rules
and user facing wording live in exactly one place.
"""
from django.shortcuts import get_object_or_404

from pages.models import Cart, CartItem

from .exceptions import (
    InvalidQuantityError,
    OutOfStockError,
    ProductUnavailableError,
)


def get_cart(user):
    """Return the user's cart, creating an empty one when needed."""
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def get_cart_items(cart):
    """Cart lines with their products prefetched, ready for the templates."""
    return (
        CartItem.objects.filter(cart=cart)
        .select_related('product')
        .order_by('product__name')
    )


def parse_quantity(raw):
    """Coerce a submitted quantity to a positive integer."""
    try:
        quantity = int(raw)
    except (TypeError, ValueError):
        raise InvalidQuantityError("Invalid quantity selected.")
    if quantity < 1:
        raise InvalidQuantityError("Quantity must be at least 1.")
    return quantity


def add_item(user, product, quantity):
    """Add ``quantity`` of ``product`` to the user's cart.

    Returns ``(cart_item, created)``.
    """
    if not product.is_available or product.stock_quantity < 1:
        raise ProductUnavailableError(
            f"{product.name} is currently out of stock or unavailable."
        )

    quantity = parse_quantity(quantity)
    if quantity > product.stock_quantity:
        raise OutOfStockError(
            f"Only {product.stock_quantity} unit(s) of {product.name} available."
        )

    cart = get_cart(user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity},
    )

    if created:
        return cart_item, created

    wanted_quantity = cart_item.quantity + quantity
    if wanted_quantity > product.stock_quantity:
        remaining = product.stock_quantity - cart_item.quantity
        raise OutOfStockError(
            f"You can only add {max(remaining, 0)} more of {product.name}."
        )

    cart_item.quantity = wanted_quantity
    cart_item.save(update_fields=['quantity'])
    return cart_item, created


def set_item_quantity(user, item_id, quantity):
    """Replace the quantity of one cart line."""
    cart_item = get_user_item(user, item_id)
    quantity = parse_quantity(quantity)
    if quantity > cart_item.product.stock_quantity:
        raise OutOfStockError(
            f"Cannot update quantity for {cart_item.product.name}. "
            f"Only {cart_item.product.stock_quantity} available."
        )
    cart_item.quantity = quantity
    cart_item.save(update_fields=['quantity'])
    return cart_item


def get_user_item(user, item_id):
    """Fetch a cart line owned by ``user``, or raise 404."""
    return get_object_or_404(
        CartItem.objects.select_related('product', 'cart'),
        id=item_id,
        cart__user=user,
    )


def remove_item(user, item_id):
    """Delete one cart line and return the removed product name."""
    cart_item = get_user_item(user, item_id)
    product_name = cart_item.product.name
    cart_item.delete()
    return product_name


def item_count(user):
    """Number of distinct products in the user's cart."""
    return CartItem.objects.filter(cart__user=user).count()


def total_price(user):
    """Cart total, or zero when the user has no cart yet."""
    cart = Cart.objects.filter(user=user).first()
    if cart is None:
        return 0
    return cart.get_total_price()


def total_price_for_items(items):
    """Total for an already fetched collection of cart lines."""
    return sum(item.get_total_price() for item in items)
