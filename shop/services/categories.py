"""Category tree queries shared by the catalog, category and search views.

The category hierarchy is a self referencing tree. Views used to walk it with a
recursive helper per request (and once per category filter), which meant several
nearly identical queries per page. Everything here reads the parent links once
and walks the tree in memory.
"""
from django.shortcuts import get_object_or_404

from pages.models import Category, Product

#: Ancestors are fetched up front so building a breadcrumb costs no extra query.
ANCESTOR_LOOKUPS = (
    'parent',
    'parent__parent',
    'parent__parent__parent',
    'parent__parent__parent__parent',
    'parent__parent__parent__parent__parent',
)


def ancestor_lookups(prefix=''):
    """``ANCESTOR_LOOKUPS`` optionally rooted at a related model.

    ``ancestor_lookups()`` walks a ``Category``'s parents while
    ``ancestor_lookups('category')`` walks a ``Product``'s category parents.
    """
    if not prefix:
        return ANCESTOR_LOOKUPS
    return tuple(f'{prefix}__{lookup}' for lookup in ANCESTOR_LOOKUPS)


def _children_by_parent():
    """Return ``{parent_id: [child_id, ...]}`` built from a single query."""
    links = Category.objects.values_list('id', 'parent_id')
    children = {}
    for category_id, parent_id in links:
        children.setdefault(parent_id, []).append(category_id)
    return children


def descendant_ids(category):
    """Return the id of ``category`` plus the ids of every category below it."""
    children = _children_by_parent()
    ids = [category.pk]
    frontier = [category.pk]
    while frontier:
        frontier = [
            child_id
            for parent_id in frontier
            for child_id in children.get(parent_id, [])
        ]
        ids.extend(frontier)
    return ids


def products_in_category(category):
    """Available products in ``category`` and all of its descendants."""
    return (
        Product.objects.filter(
            category__in=descendant_ids(category),
            is_available=True,
        )
        .select_related('brand')
        .order_by('name')
    )


def get_category(slug):
    """Fetch a category with its ancestors already loaded, or raise 404."""
    return get_object_or_404(
        Category.objects.select_related(*ANCESTOR_LOOKUPS),
        slug=slug,
    )


def breadcrumb_for(category):
    """Ancestor chain for ``category``, root first, with ``category`` last."""
    breadcrumb = []
    current = category
    while current is not None:
        breadcrumb.insert(0, current)
        current = current.parent
    return breadcrumb


def top_level_ancestor_id(category_id):
    """Id of the top level ancestor of ``category_id``, or ``None``.

    Vendor forms render the category tree as one accordion per top level
    category, so they need both the selected category id and the id of the
    panel that has to be expanded.
    """
    if not category_id:
        return None

    try:
        category = Category.objects.select_related(*ANCESTOR_LOOKUPS).get(
            pk=category_id
        )
    except (Category.DoesNotExist, ValueError, TypeError):
        return None

    return breadcrumb_for(category)[0].pk


def resolve_subtree(category_id):
    """Return the ids of the category tree for ``category_id``, or ``None``.

    ``None`` means the category does not exist, which lets search views ignore
    an unknown filter instead of failing the whole request.
    """
    try:
        category = Category.objects.get(pk=category_id)
    except (Category.DoesNotExist, ValueError, TypeError):
        return None
    return descendant_ids(category)
