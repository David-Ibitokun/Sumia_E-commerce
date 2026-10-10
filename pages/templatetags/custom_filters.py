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


@register.simple_tag
def querystring(query_dict, **kwargs):
    """Return a query string with the given parameters added/updated.

    Usage: {% querystring request.GET page=2 %} or
           {% querystring request.GET page=2 sort='name' %}
    """
    if not hasattr(query_dict, 'copy'):
        return ''
    new_query = query_dict.copy()
    for key, value in kwargs.items():
        new_query[key] = value
    return new_query.urlencode()