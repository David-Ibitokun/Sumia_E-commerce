from django.urls import path
from .views import (
    category_detail, shop, singleProduct, product_detail, view_cart,
    add_product, product_list, edit_product, delete_product,
    brand_detail, brand_list,
    add_to_cart, remove_from_cart, update_cart_quantity,
    checkout,
    search,
    wishlist_view, add_to_wishlist, remove_from_wishlist,
    vendor_orders, vendor_order_detail,
    recent_order, order_detail,
    product_list as product_list_view,
)

urlpatterns = [
    path('shop/', shop, name='shop'),
    path('category/<slug:slug>/', category_detail, name='category_detail'),

    path('product/add/', add_product, name='add_product'),
    path('product/list/', product_list, name='product_list'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),
    path('products/<slug:slug>/', singleProduct, name='singleProduct'),
    path('product/<slug:slug>/edit/', edit_product, name='edit_product'),
    path('product/<slug:slug>/delete/', delete_product, name='delete_product'),

    path('brands/', brand_list, name='brand_list'),
    path('brands/<slug:slug>/', brand_detail, name='brand_detail'),
    path('brands/<int:pk>/', brand_detail, name='brand_detail_by_id'),

    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', view_cart, name='cart'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', update_cart_quantity, name='update_cart_quantity'),

    path('checkout/', checkout, name='checkout'),

    path('search/', search, name='search'),

    path('wishlist/', wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', remove_from_wishlist, name='remove_from_wishlist'),

    path('vendor/orders/', vendor_orders, name='vendor_orders'),
    path('vendor/orders/<str:order_number>/', vendor_order_detail, name='vendor_order_detail'),

    path('my-orders/', recent_order, name='recent_order'),
    path('my-orders/<str:order_number>/', order_detail, name='users_order_detail'),
    path('orders/<str:order_number>/', order_detail, name='order_detail'),
]
