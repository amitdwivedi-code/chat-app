from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Safely get dictionary[key] where key may be string/int.
    Returns None if not found.
    """
    try:
        return dictionary.get(int(key))
    except Exception:
        return None