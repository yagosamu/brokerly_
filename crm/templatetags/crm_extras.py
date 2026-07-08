from django import template


register = template.Library()


@register.filter
def dict_get(mapping, key):
    """Return mapping[key] handling both str and int keys defensively."""
    if mapping is None:
        return None
    try:
        if key in mapping:
            return mapping[key]
    except TypeError:
        return None
    try:
        return mapping.get(str(key))
    except AttributeError:
        return None
