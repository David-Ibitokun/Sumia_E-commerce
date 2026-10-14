"""Read-only queries for the product catalog."""
from django.db.models import Case, F, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404

from pages.models import Product

from . import categories

RELATED_PRODUCT_LIMIT = 4
SEARCH_RESULT_LIMIT = 8
PRODUCT_FIELDS = ('category', 'brand')


def product_lookup_fields():
    """Relations needed to render a product card without extra queries."""
    return PRODUCT_FIELDS + categories.ancestor_lookups('category')


def available_products():
    """Every product a shopper may see, ordered by name."""
    return (
        Product.objects.filter(is_available=True)
        .select_related(*PRODUCT_FIELDS)
        .order_by('name')
    )


def latest_products(limit=12):
    """Newest products for the landing page."""
    return (
        Product.objects.filter(is_available=True)
        .select_related(*PRODUCT_FIELDS)
        .order_by('-created_at')[:limit]
    )


def products_for_brand(brand):
    """Available products belonging to ``brand``."""
    return (
        Product.objects.filter(brand=brand, is_available=True)
        .select_related(*PRODUCT_FIELDS)
        .order_by('-created_at')
    )


def get_product(slug):
    """Fetch a product for its detail page, or raise 404."""
    return get_object_or_404(
        Product.objects.select_related(*product_lookup_fields()),
        slug=slug,
    )


def related_products(product, limit=RELATED_PRODUCT_LIMIT):
    """A handful of other products from the same category."""
    if product.category_id is None:
        return Product.objects.none()
    return (
        Product.objects.filter(category_id=product.category_id, is_available=True)
        .exclude(pk=product.pk)
        .select_related(*PRODUCT_FIELDS)
        .order_by('?')[:limit]
    )


def search_products(query, category_id=None, only_available=False):
    """Search products by name, description, category, tag or brand.

    Shared by the full search page and the AJAX live search so both stay in sync.
    Results are ranked by relevance: exact-name matches score highest, brand and
    category matches score next, and description matches score lowest.  An
    empty query returns all (optionally available) products ordered by recency.
    """
    queryset = Product.objects.all()
    if only_available:
        queryset = queryset.filter(is_available=True)

    if query:
        # Annotate match flags first so each LIKE is evaluated only once,
        # then filter on the flags (avoids the double-EVALUATE problem where
        # the original Case/When re-ran every icontains condition from the
        # WHERE clause).
        queryset = queryset.annotate(
            name_match=Case(
                When(name__icontains=query, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            brand_match=Case(
                When(brand__name__icontains=query, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            category_match=Case(
                When(category__name__icontains=query, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            tag_match=Case(
                When(tags__name__icontains=query, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            description_match=Case(
                When(description__icontains=query, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        ).filter(
            Q(name_match=1)
            | Q(brand_match=1)
            | Q(category_match=1)
            | Q(tag_match=1)
            | Q(description_match=1)
        ).distinct().annotate(
            relevance=(
                F('name_match') * 4
                + F('brand_match') * 2
                + F('category_match') * 2
                + F('tag_match') * 2
                + F('description_match') * 1
            ),
        ).order_by('-relevance', '-created_at')

    if category_id:
        category_ids = categories.resolve_subtree(category_id)
        if category_ids is None:
            return queryset.none()
        queryset = queryset.filter(category__in=category_ids)

    return queryset.select_related(*PRODUCT_FIELDS)


