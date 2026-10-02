"""Checkout: shipping/payment form and order placement.

All validation lives in `shop.forms.CheckoutForm`; the view only turns a valid
form into an order through `shop.services.orders`.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from shop.forms import CheckoutForm
from shop.services import cart as cart_service
from shop.services import orders as order_service
from shop.services.exceptions import ShopServiceError


@login_required(login_url='login')
def checkout(request):
    """Review the cart and place the order."""
    cart = cart_service.get_cart(request.user)
    cart_items = cart_service.get_cart_items(cart)

    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': cart_service.total_price_for_items(cart_items),
    }

    if request.method != 'POST':
        return render(
            request,
            'checkout/checkout.html',
            {
                **context,
                'form': CheckoutForm(
                    initial=CheckoutForm.shipping_defaults(request.user)
                ),
            },
        )

    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return render(
            request, 'checkout/checkout.html', {**context, 'form': form}
        )

    try:
        order = order_service.create_order(
            request.user, cart, form.shipping_data()
        )
    except ShopServiceError as error:
        messages.error(request, str(error))
        return render(
            request, 'checkout/checkout.html', {**context, 'form': form}
        )

    messages.success(request, "Your order has been placed successfully!")
    return redirect('order_detail', order_number=order.order_number)
