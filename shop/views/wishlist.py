"""Wishlist page and wishlist mutations (non-AJAX)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from pages.models import Product

from shop.services import wishlist as wishlist_service

from .utils import redirect_back


@login_required(login_url='login')
def wishlist_view(request):
    """Show the signed in user's wishlist."""
    return render(
        request,
        'catalog/wishlist.html',
        {'wishlist_items': wishlist_service.items_for_user(request.user)},
    )


@login_required(login_url='login')
def add_to_wishlist(request, product_id):
    """Save a product to the wishlist from a plain link."""
    product = get_object_or_404(Product, id=product_id)

    if wishlist_service.add_item(request.user, product):
        messages.success(request, f"{product.name} added to your wishlist!")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")

    return redirect_back(request, 'wishlist')


@login_required(login_url='login')
def remove_from_wishlist(request, item_id):
    """Remove a product from the wishlist."""
    product_name = wishlist_service.remove_item(request.user, item_id)
    messages.info(request, f"{product_name} removed from your wishlist.")
    return redirect('wishlist')
