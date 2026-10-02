"""Cached navigation data shared by every template."""
from django.core.cache import cache

from pages.models import Category

#: Bumped/invalidated by pages.signals whenever a category changes.
CATEGORY_TREE_CACHE_KEY = 'pages:top_level_categories'
CATEGORY_TREE_CACHE_TIMEOUT = 60 * 60


def get_top_level_categories():
    """Top level categories with their children, cached across requests.

    The navigation tree is identical for every visitor, so it is fetched once
    and reused until a category is created, changed or removed.
    """
    categories = cache.get(CATEGORY_TREE_CACHE_KEY)
    if categories is None:
        categories = list(
            Category.objects.filter(
                parent__isnull=True, is_active=True
            ).prefetch_related('subcategories').order_by('name')
        )
        cache.set(CATEGORY_TREE_CACHE_KEY, categories, CATEGORY_TREE_CACHE_TIMEOUT)
    return categories


def invalidate_category_tree(**kwargs):
    """Drop the cached tree; wired up in `pages.apps.PagesConfig.ready`."""
    cache.delete(CATEGORY_TREE_CACHE_KEY)


def categories_for_search(request):
    """Make the category tree available to every template."""
    return {'top_level_categories': get_top_level_categories()}
