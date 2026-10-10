"""Public storefront pages: shop, product, category and brand."""
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from pages.models import Brand

from shop.services import catalog, categories, pagination


def shop(request):
    """List every available product."""
    products = catalog.available_products()
    page_obj, paginator = pagination.paginate_queryset(request, products)
    return render(
        request,
        'catalog/shop.html',
        {
            'page_obj': page_obj,
            'paginator': paginator,
            'products': page_obj.object_list,
        },
    )


def product_detail(request, slug):
    """Show one product with its breadcrumb and related items."""
    product = catalog.get_product(slug)
    return render(
        request,
        'catalog/product_detail.html',
        {
            'product': product,
            'breadcrumb': categories.breadcrumb_for(product.category),
            'products': catalog.related_products(product),
        },
    )


def category_detail(request, slug):
    """List the products of a category and everything below it."""
    category = categories.get_category(slug)
    products = categories.products_in_category(category)
    page_obj, paginator = pagination.paginate_queryset(request, products)
    return render(
        request,
        'catalog/category_detail.html',
        {
            'category': category,
            'page_obj': page_obj,
            'paginator': paginator,
            'products': page_obj.object_list,
            'breadcrumb': categories.breadcrumb_for(category),
        },
    )


def brand_list(request):
    """List all brands."""
    brands = Brand.objects.order_by('name')
    page_obj, paginator = pagination.paginate_queryset(request, brands)
    return render(
        request,
        'catalog/brand_list.html',
        {
            'page_obj': page_obj,
            'paginator': paginator,
            'brands': page_obj.object_list,
        },
    )


def brand_detail(request, slug=None, pk=None):
    """List the products of a brand, addressed by slug or primary key."""
    brand = _get_brand(slug=slug, pk=pk)
    products = catalog.products_for_brand(brand)
    page_obj, paginator = pagination.paginate_queryset(request, products)
    return render(
        request,
        'catalog/brand_detail.html',
        {
            'brand': brand,
            'page_obj': page_obj,
            'paginator': paginator,
            'products': page_obj.object_list,
        },
    )


def _get_brand(slug=None, pk=None):
    if slug:
        return get_object_or_404(Brand, slug=slug)
    if pk:
        return get_object_or_404(Brand, pk=pk)
    raise Http404('No brand identifier provided.')