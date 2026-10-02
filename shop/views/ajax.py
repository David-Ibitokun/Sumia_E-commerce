"""JSON endpoints consumed by static/js/ajax_ecommerce.js.

They mirror the non-AJAX cart and wishlist views but answer with the payload
the JavaScript expects: ``status``, ``message`` and the counters it repaints.
"""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from pages.models import CartItem, Product

from shop.services import cart as cart_service
from shop.services import catalog, wishlist as wishlist_service
from shop.services.exceptions import ShopServiceError

from .utils import json_error

LOGIN_REQUIRED_MESSAGE = "Please log in to continue."
SEARCH_RESULT_LIMIT = 8


@require_GET
def ajax_cart_count(request):
    """Current number of cart lines for the navbar badge."""
    count = cart_service.item_count(request.user) if request.user.is_authenticated else 0
    return JsonResponse({'cart_count': count})


@require_POST
def ajax_add_to_cart(request, product_id):
    """Add a product to the cart and return the refreshed counters."""
    if not request.user.is_authenticated:
        return json_error(LOGIN_REQUIRED_MESSAGE, status=401)

    product = get_object_or_404(Product, id=product_id)
    try:
        cart_service.add_item(request.user, product, request.POST.get('quantity', 1))
    except ShopServiceError as error:
        return json_error(str(error))

    return JsonResponse(
        {
            'status': 'success',
            'message': f"Added {product.name} to your cart.",
            'cart_count': cart_service.item_count(request.user),
            'cart_total': str(cart_service.total_price(request.user)),
        }
    )


@require_POST
def ajax_remove_from_cart(request, item_id):
    """Remove a cart line and report whether the cart is now empty."""
    if not request.user.is_authenticated:
        return json_error(LOGIN_REQUIRED_MESSAGE, status=401)

    product_name = cart_service.remove_item(request.user, item_id)
    remaining = CartItem.objects.filter(cart__user=request.user).count()

    return JsonResponse(
        {
            'status': 'success',
            'message': f"Removed {product_name} from cart.",
            'cart_count': remaining,
            'cart_total': str(cart_service.total_price(request.user)),
            'cart_empty': remaining == 0,
        }
    )


@require_POST
def ajax_update_cart_quantity(request, item_id):
    """Set a cart line's quantity and return its subtotal plus the new total."""
    if not request.user.is_authenticated:
        return json_error(LOGIN_REQUIRED_MESSAGE, status=401)

    try:
        cart_item = cart_service.set_item_quantity(
            request.user, item_id, request.POST.get('quantity', 1)
        )
    except ShopServiceError as error:
        return json_error(str(error))

    return JsonResponse(
        {
            'status': 'success',
            'message': 'Quantity updated.',
            'cart_count': cart_service.item_count(request.user),
            'item_subtotal': str(cart_item.get_total_price()),
            'cart_total': str(cart_service.total_price(request.user)),
        }
    )


@require_POST
def ajax_add_to_wishlist(request, product_id):
    """Save a product to the wishlist, or confirm it is already there."""
    if not request.user.is_authenticated:
        return json_error("Please log in to add items to your wishlist.", status=401)

    product = get_object_or_404(Product, id=product_id)
    created = wishlist_service.add_item(request.user, product)

    return JsonResponse(
        {
            'status': 'success' if created else 'info',
            'message': (
                f"Added {product.name} to your wishlist."
                if created
                else f"{product.name} is already in your wishlist."
            ),
            'in_wishlist': True,
            'wishlist_count': wishlist_service.count_for_user(request.user),
        }
    )


@require_POST
def ajax_remove_from_wishlist(request, item_id):
    """Remove a wishlist line and return the new wishlist size."""
    if not request.user.is_authenticated:
        return json_error(LOGIN_REQUIRED_MESSAGE, status=401)

    product_name = wishlist_service.remove_item(request.user, item_id)

    return JsonResponse(
        {
            'status': 'success',
            'message': f"Removed {product_name} from your wishlist.",
            'in_wishlist': False,
            'wishlist_count': wishlist_service.count_for_user(request.user),
        }
    )


@require_GET
def ajax_search(request):
    """Type-ahead product suggestions for the navbar search box."""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')

    products = (
        catalog.search_products(query, category_id, only_available=True)
        if len(query) >= 2
        else Product.objects.none()
    )

    return JsonResponse(
        {
            'query': query,
            'results': [_serialize(product) for product in products[:SEARCH_RESULT_LIMIT]],
        }
    )


def _serialize(product):
    return {
        'name': product.name,
        'slug': product.slug,
        'detail_url': reverse('product_detail', kwargs={'slug': product.slug}),
        'price': str(product.price),
        'discount_price': str(product.discount_price) if product.discount_price else None,
        'image_url': product.image.url if product.image else None,
    }
