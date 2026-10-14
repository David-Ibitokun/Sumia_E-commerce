"""Full search results page."""
from django.shortcuts import render

from pages.models import Product
from shop.services import catalog, pagination


def search(request):
    """Search products, optionally narrowed to one category subtree."""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')

    if query:
        products = catalog.search_products(query, category_id)
    else:
        products = Product.objects.none()

    page_obj, paginator = pagination.paginate_queryset(request, products)

    return render(
        request,
        'catalog/search_results.html',
        {
            'query': query,
            'page_obj': page_obj,
            'paginator': paginator,
            'products': page_obj.object_list,
            'total_results': paginator.count,
            'selected_category_id': category_id,
        },
    )