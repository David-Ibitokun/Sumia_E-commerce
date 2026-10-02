"""Views for the shop app, grouped by the feature they serve.

    public.py    storefront pages: shop, product, category, brand
    catalog.py   vendor product management (add, edit, delete, list)
    cart.py      cart page and cart mutations
    checkout.py  shipping form and order placement
    orders.py    order history for customers
    vendors.py   order views scoped to a vendor's own products
    wishlist.py  wishlist page and mutations
    search.py    full search results page
    ajax.py      JSON endpoints used by static/js/ajax_ecommerce.js
    utils.py     helpers shared by the modules above

`shop.urls` wires these modules to routes; importing a view module directly
(`from shop.views.cart import cart_view`) is the expected way to reach them.
"""
