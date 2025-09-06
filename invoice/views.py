# Django core imports
from django.urls import reverse,reverse_lazy
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.db.models import Q

# Authentication and permissions
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Class-based views
from django.views.generic import (
    DetailView, CreateView, UpdateView, DeleteView
)
from django.views.generic.edit import FormView

# Third-party packages
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

# Local app imports
from .models import Invoice
from accounts.models import Customer
from store.models import Item
from .tables import InvoiceTable
from .forms import InvoiceForm


class InvoiceListView(LoginRequiredMixin, ExportMixin, SingleTableView):
    """
    View for listing invoices with table export functionality.
    """
    model = Invoice
    table_class = InvoiceTable
    template_name = 'invoice/invoicelist.html'
    context_object_name = 'invoices'
    paginate_by = 10
    table_pagination = False  # Disable table pagination


class InvoiceDetailView(DetailView):
    """
    View for displaying invoice details.
    """
    model = Invoice
    template_name = 'invoice/invoicedetail.html'

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful action.
        """
        return reverse('invoice-detail', kwargs={'slug': self.object.pk})


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    template_name = 'invoice/invoice.html'
    form_class = InvoiceForm

    def get_success_url(self):
        return reverse_lazy('invoicelist')

    def form_valid(self, form):
        # The item field should now be a proper Item object due to clean_item()
        item = form.cleaned_data.get('item')
        if item:
            form.instance.price_per_item = item.price
        
        customer = form.cleaned_data.get('customer_name')
        if customer:
            form.instance.contact_number = customer.phone or form.cleaned_data.get('contact_number', '')
        
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form errors:", form.errors)  # Debugging
        return super().form_invalid(form)

# Autocomplete views
@require_GET
def autocomplete_customers(request):
    query = request.GET.get('q', '')
    if query:
        customers = Customer.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )[:10]
        results = [
            {
                'id': customer.id,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'phone': customer.phone,
                'email': customer.email,
                'address': customer.address,
                'loyalty_points': customer.loyalty_points,
                'text': f"{customer.first_name} {customer.last_name} ({customer.phone})"
            }
            for customer in customers
        ]
    else:
        results = []
    return JsonResponse({'results': results})

@require_GET
def autocomplete_items(request):
    query = request.GET.get('q', '')
    if query:
        items = Item.objects.filter(name__icontains=query)[:10]
        results = [
            {
                'id': item.id,
                'name': item.name,
                'quantity': item.quantity,
                'price_per_item': item.price,
                'text': f"{item.name} ({item.quantity} available) - Tsh {item.price:,.2f}"
            }
            for item in items
        ]
    else:
        results = []
    return JsonResponse({'results': results})

class InvoiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating an existing invoice.
    """
    model = Invoice
    template_name = 'invoice/invoiceupdate.html'
    fields = [
        'customer_name', 'contact_number', 'item',
        'price_per_item', 'quantity', 'shipping'
    ]

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful update.
        """
        return reverse('invoicelist')

    def test_func(self):
        """
        Determine if the user has permission to update the invoice.
        """
        return self.request.user.is_superuser


class InvoiceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting an invoice.
    """
    model = Invoice
    template_name = 'invoice/invoicedelete.html'
    success_url = '/products'  # Can be overridden in get_success_url()

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful deletion.
        """
        return reverse('invoicelist')

    def test_func(self):
        """
        Determine if the user has permission to delete the invoice.
        """
        return self.request.user.is_superuser
