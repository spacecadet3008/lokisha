from django import template

register = template.Library()

@register.filter
def sum_attr(queryset, attr):
    """Sum a specific attribute from a queryset"""
    return sum(getattr(item, attr) for item in queryset)

@register.filter
def sum_items_total(delivery):
    """Calculate total value of all items in a delivery"""
    return sum(item.total_price for item in delivery.items.all())