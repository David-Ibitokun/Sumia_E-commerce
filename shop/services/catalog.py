"""Read-only queries for the product catalog."""
import re
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


def search_products(query, category_id=None, only_available=False, sort_by='relevance'):
    """Advanced search across products with multi-word tokenization and relevance scoring.

    Shared by full search page and AJAX live search so both stay in sync.
    Ranks results based on exact matches, word occurrences in name/brand/category/tags,
    and description fallback. Supports sorting and category subtree filtering.
    """
    queryset = Product.objects.all()
    if only_available:
        queryset = queryset.filter(is_available=True)

    if query:
        cleaned_query = query.strip()
        # Extract individual search tokens
        tokens = [t for t in re.findall(r'[\w]+', cleaned_query.lower()) if len(t) >= 2]
        if not tokens and cleaned_query:
            tokens = [cleaned_query.lower()]

        # Relevance scoring annotations
        annotations = {
            'exact_name': Case(
                When(name__iexact=cleaned_query, then=Value(50)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            'starts_with_name': Case(
                When(name__istartswith=cleaned_query, then=Value(30)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            'phrase_name': Case(
                When(name__icontains=cleaned_query, then=Value(20)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            'phrase_brand': Case(
                When(brand__name__icontains=cleaned_query, then=Value(18)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            'phrase_category': Case(
                When(category__name__icontains=cleaned_query, then=Value(15)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            'phrase_tags': Case(
                When(tags__name__icontains=cleaned_query, then=Value(12)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            'phrase_description': Case(
                When(description__icontains=cleaned_query, then=Value(5)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        }

        # Build token-level match conditions
        relevance_expr = (
            F('exact_name')
            + F('starts_with_name')
            + F('phrase_name')
            + F('phrase_brand')
            + F('phrase_category')
            + F('phrase_tags')
            + F('phrase_description')
        )

        for idx, token in enumerate(tokens[:5]):  # Up to 5 tokens for performance
            token_key = f'tok_{idx}'
            annotations[token_key] = Case(
                When(name__icontains=token, then=Value(8)),
                When(brand__name__icontains=token, then=Value(5)),
                When(category__name__icontains=token, then=Value(4)),
                When(tags__name__icontains=token, then=Value(3)),
                When(description__icontains=token, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
            relevance_expr = relevance_expr + F(token_key)

        # Primary filter: Conjunctive match (products matching all tokens or the full phrase)
        conjunctive_filter = Q(name__icontains=cleaned_query) | Q(brand__name__icontains=cleaned_query) | Q(description__icontains=cleaned_query)
        if tokens:
            all_tokens_q = Q()
            for token in tokens:
                token_q = (
                    Q(name__icontains=token)
                    | Q(brand__name__icontains=token)
                    | Q(category__name__icontains=token)
                    | Q(tags__name__icontains=token)
                    | Q(description__icontains=token)
                )
                all_tokens_q &= token_q
            conjunctive_filter |= all_tokens_q

        filtered = queryset.filter(conjunctive_filter)
        if not filtered.exists():
            # Fallback to disjunctive match (matching any token) so search doesn't return empty
            any_token_q = Q()
            for token in tokens:
                any_token_q |= (
                    Q(name__icontains=token)
                    | Q(brand__name__icontains=token)
                    | Q(category__name__icontains=token)
                    | Q(tags__name__icontains=token)
                    | Q(description__icontains=token)
                )
            filtered = queryset.filter(any_token_q)

        queryset = filtered.annotate(**annotations).distinct().annotate(
            relevance=relevance_expr
        )

        # Apply sorting
        if sort_by in ('price_asc', 'price_low'):
            queryset = queryset.order_by('price', '-relevance')
        elif sort_by in ('price_desc', 'price_high'):
            queryset = queryset.order_by('-price', '-relevance')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at', '-relevance')
        else:
            queryset = queryset.order_by('-relevance', '-created_at')

    if category_id:
        category_ids = categories.resolve_subtree(category_id)
        if category_ids is None:
            return queryset.none()
        queryset = queryset.filter(category__in=category_ids)

    return queryset.select_related(*PRODUCT_FIELDS)



