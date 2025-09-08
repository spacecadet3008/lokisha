# Create this in a utils.py file or at the top of views.py
def sum_attr(queryset, attr):
    """Sum a specific attribute from a queryset"""
    return sum(getattr(item, attr) for item in queryset)

# Add to your view context
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    # ...
    context['delivery_items_total'] = sum_attr(self.object.items.all(), 'total_price')
    return context