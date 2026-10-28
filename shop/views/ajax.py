"""JSON endpoints consumed by static/js/ajax_ecommerce.js.

They mirror the non-AJAX cart and wishlist views but answer with the payload
the JavaScript expects: ``status``, ``message`` and the counters it repaints.
"""
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from pages.models import CartItem, Product

from shop.services import cart as cart_service
from shop.services import catalog, wishlist as wishlist_service
from pages.ratelimit import ratelimit
from shop.services.exceptions import ShopServiceError

from .utils import json_error

LOGIN_REQUIRED_MESSAGE = "Please log in to continue."
SEARCH_RESULT_LIMIT = 8
SEARCH_CACHE_TIMEOUT = 300


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
    remaining = cart_service.item_count(request.user)

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
        return json_error(LOGIN_REQUIRED_MESSAGE, status=401)

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
@ratelimit(capacity=30, refill_rate=5.0, key_prefix='rl_search', is_json=True)
def ajax_search(request):
    """Type-ahead product suggestions for the navbar search box."""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')

    if len(query) >= 2:
        cache_key = f'ajax_search:q={query}:cat={category_id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return JsonResponse(cached)

        products = catalog.search_products(query, category_id, only_available=True)
        total = products.count()
        limited = products[:SEARCH_RESULT_LIMIT]

        result = {
            'query': query,
            'total': total,
            'has_more': total > SEARCH_RESULT_LIMIT,
            'results': [_serialize(product) for product in limited],
        }
        cache.set(cache_key, result, SEARCH_CACHE_TIMEOUT)
        return JsonResponse(result)
    else:
        return JsonResponse(
            {
                'query': query,
                'total': 0,
                'has_more': False,
                'results': [],
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
        'category_name': product.category.name if product.category else '',
        'brand_name': product.brand.name if product.brand else '',
        'discount_percent': product.get_discount_percent() if product.discount_price else 0,
    }


@require_GET
def ajax_quick_view(request, product_id):
    """Retrieve full product details for interactive quick view modal."""
    product = get_object_or_404(Product, id=product_id)
    return JsonResponse({
        'status': 'success',
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'detail_url': reverse('product_detail', kwargs={'slug': product.slug}),
        'category': product.category.name if product.category else 'General',
        'brand': product.brand.name if product.brand else None,
        'description': product.description,
        'price': f"{product.price:,.2f}",
        'discount_price': f"{product.discount_price:,.2f}" if product.discount_price else None,
        'discount_percent': product.get_discount_percent() if product.discount_price else 0,
        'is_available': product.is_available and product.stock_quantity > 0,
        'stock_quantity': product.stock_quantity,
        'image_url': product.image.url if product.image else None,
        'add_to_cart_url': reverse('ajax_add_to_cart', kwargs={'product_id': product.id}),
        'add_to_wishlist_url': reverse('ajax_add_to_wishlist', kwargs={'product_id': product.id}),
    })
