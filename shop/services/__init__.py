"""Business logic for the shop app.

Views stay thin: they resolve a request, call one of these services and render
(or serialise) the result. Nothing in here touches ``HttpRequest`` or returns
an ``HttpResponse``, which keeps the rules testable on their own.

Modules:
    categories  category tree lookups (descendants, breadcrumbs)
    catalog     product queries (listing, detail, related, search)
    cart        cart mutations and totals
    orders      order placement and order queries
    wishlist    wishlist mutations and counts
    exceptions  domain errors the views translate into messages
"""
