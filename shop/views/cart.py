"""Cart page and cart mutations (non-AJAX)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from pages.models import Product

from shop.services import cart as cart_service
from shop.services.exceptions import ShopServiceError

from .utils import redirect_back


def cart_view(request):
    """Show the cart. Guests see an empty cart instead of a redirect."""
    if request.user.is_authenticated:
        cart = cart_service.get_cart(request.user)
        cart_items = cart_service.get_cart_items(cart)
        total_price = cart_service.total_price_for_items(cart_items)
    else:
        cart_items = []
        total_price = 0

    return render(
        request,
        'checkout/cart.html',
        {'cart_items': cart_items, 'total_price': total_price},
    )


@login_required(login_url='login')
def add_to_cart(request, product_id):
    """Add a product to the cart from a plain HTML form."""
    product = get_object_or_404(Product, id=product_id)

    try:
        _, created = cart_service.add_item(
            request.user, product, request.POST.get('quantity', 1)
        )
    except ShopServiceError as error:
        messages.error(request, str(error))
    else:
        if created:
            messages.success(request, f"{product.name} added to your cart.")
        else:
            messages.success(request, f"Updated {product.name} quantity in your cart.")

    return redirect_back(request, 'cart')


@login_required(login_url='login')
def remove_from_cart(request, item_id):
    """Remove one line from the cart."""
    product_name = cart_service.remove_item(request.user, item_id)
    messages.info(request, f"{product_name} removed from your cart.")
    return redirect('cart')


@login_required(login_url='login')
def update_cart_quantity(request, item_id):
    """Set the quantity of one cart line from a plain HTML form."""
    if request.method != 'POST':
        return redirect('cart')

    try:
        cart_item = cart_service.set_item_quantity(
            request.user, item_id, request.POST.get('quantity', 1)
        )
    except ShopServiceError as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request, f"Quantity for {cart_item.product.name} updated."
        )

    return redirect('cart')
