"""Full search results page."""
from django.shortcuts import render

from shop.services import catalog


def search(request):
    """Search products, optionally narrowed to one category subtree."""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')

    products = catalog.search_products(query, category_id)

    return render(
        request,
        'catalog/search_results.html',
        {
            'query': query,
            'products': products,
            'selected_category_id': category_id,
        },
    )
