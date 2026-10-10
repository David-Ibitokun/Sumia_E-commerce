"""Pagination utilities for list views."""

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


DEFAULT_PAGE_SIZE = 12
MAX_PAGE_SIZE = 100


def paginate_queryset(request, queryset, page_size=DEFAULT_PAGE_SIZE):
    """Paginate a queryset and return (page_obj, paginator).

    Args:
        request: HttpRequest with ?page= query parameter.
        queryset: Django QuerySet to paginate.
        page_size: Number of items per page (default 12, max 100).

    Returns:
        tuple: (page_obj, paginator) where page_obj is a Page instance.
    """
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)
    paginator = Paginator(queryset, page_size)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj, paginator