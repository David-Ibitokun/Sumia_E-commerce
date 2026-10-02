"""Template filters shared by the project templates."""

from django import template

register = template.Library()


@register.filter
def get_item(query_set, pk_value):
    """Return the object with ``pk_value`` from a queryset, or None.

    Used by templates that need one specific related row instead of a full
    queryset lookup.
    """
    try:
        return query_set.filter(id=pk_value).first()
    except (AttributeError, TypeError, ValueError):
        return None