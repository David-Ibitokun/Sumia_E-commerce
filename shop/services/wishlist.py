"""Wishlist queries and mutations."""
from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from pages.models import Wishlist


def items_for_user(user):
    """A user's wishlist lines, newest first, with products prefetched."""
    return (
        Wishlist.objects.filter(user=user)
        .select_related('product')
        .order_by('-added_at')
    )


def add_item(user, product):
    """Add a product to the wishlist.

    Returns ``True`` when the product was added, ``False`` when it was already
    saved. ``get_or_create`` covers the normal case; the integrity error only
    happens on a concurrent double submit.
    """
    try:
        _, created = Wishlist.objects.get_or_create(user=user, product=product)
    except IntegrityError:
        return False
    return created


def remove_item(user, item_id):
    """Remove a wishlist line and return the removed product name."""
    wishlist_item = get_object_or_404(
        Wishlist.objects.select_related('product'),
        id=item_id,
        user=user,
    )
    product_name = wishlist_item.product.name
    wishlist_item.delete()
    return product_name


def count_for_user(user):
    """Number of products on the user's wishlist."""
    return Wishlist.objects.filter(user=user).count()
