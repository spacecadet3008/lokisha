from django import template

register = template.Library()

@register.filter
def sum_attr(queryset, attr_name):
    """Sum a specific attribute from a queryset"""
    return sum(getattr(item, attr_name, 0) for item in queryset)