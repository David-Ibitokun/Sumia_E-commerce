"""Routes for the shop app.

Views are grouped by feature in `shop.views`; names are snake_case. A couple of
legacy route names are kept as aliases so older links and bookmarks keep
working; new code should use the canonical names.
"""
from django.urls import path

from .views import ajax, cart, catalog, checkout, orders, public, search
from .views import vendors, wishlist

urlpatterns = [
    # Vendor product management (literal routes first so they are not captured
    # by the `product/<slug:slug>/` pattern below).
    path('product/add/', catalog.add_product, name='add_product'),
    path('product/list/', catalog.product_list, name='product_list'),

    # Storefront
    path('shop/', public.shop, name='shop'),
    path('category/<slug:slug>/', public.category_detail, name='category_detail'),
    path('product/<slug:slug>/edit/', catalog.edit_product, name='edit_product'),
    path('product/<slug:slug>/delete/', catalog.delete_product, name='delete_product'),
    path('product/<slug:slug>/', public.product_detail, name='product_detail'),
    path('products/<slug:slug>/', public.product_detail, name='singleProduct'),  # legacy alias
    path('brands/', public.brand_list, name='brand_list'),
    path('brands/id/<int:pk>/', public.brand_detail, name='brand_detail_by_id'),
    path('brands/<slug:slug>/', public.brand_detail, name='brand_detail'),

    # Cart
    path('cart/', cart.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', cart.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', cart.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', cart.update_cart_quantity, name='update_cart_quantity'),

    # Checkout
    path('checkout/', checkout.checkout, name='checkout'),

    # Search
    path('search/', search.search, name='search'),

    # Wishlist
    path('wishlist/', wishlist.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', wishlist.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', wishlist.remove_from_wishlist, name='remove_from_wishlist'),

    # Customer orders
    path('my-orders/', orders.order_list, name='order_list'),
    path('orders/<str:order_number>/', orders.order_detail, name='order_detail'),

    # Vendor orders
    path('vendor/orders/', vendors.vendor_orders, name='vendor_orders'),
    path('vendor/orders/<str:order_number>/', vendors.vendor_order_detail, name='vendor_order_detail'),

    # AJAX endpoints consumed by static/js/ajax_ecommerce.js
    path('ajax/cart/count/', ajax.ajax_cart_count, name='ajax_cart_count'),
    path('ajax/cart/add/<int:product_id>/', ajax.ajax_add_to_cart, name='ajax_add_to_cart'),
    path('ajax/cart/remove/<int:item_id>/', ajax.ajax_remove_from_cart, name='ajax_remove_from_cart'),
    path('ajax/cart/update/<int:item_id>/', ajax.ajax_update_cart_quantity, name='ajax_update_cart_quantity'),
    path('ajax/wishlist/add/<int:product_id>/', ajax.ajax_add_to_wishlist, name='ajax_add_to_wishlist'),
    path('ajax/wishlist/remove/<int:item_id>/', ajax.ajax_remove_from_wishlist, name='ajax_remove_from_wishlist'),
    path('ajax/search/', ajax.ajax_search, name='ajax_search'),
]
