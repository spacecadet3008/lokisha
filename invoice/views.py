# Django core imports
from django.urls import reverse,reverse_lazy
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.db.models import Q
from django.forms import formset_factory

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
from .forms import InvoiceForm,InvoiceItemFormSet
from django.shortcuts import get_object_or_404
from django.http import Http404


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


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoice/invoice_detail.html'
    context_object_name = 'invoice'
    pk_url_kwarg = 'pk'  # Default is 'pk', but you can change it if needed
    sucess_url = reverse_lazy('invoicelist')

    def get_queryset(self):
        """
        Optimize database queries by prefetching related data
        """
        return Invoice.objects.prefetch_related(
            'items__item'
        ).select_related(
            'customer_name'
        )

    def get_object(self, queryset=None):
        """
        Get the invoice object with additional checks
        """
        if queryset is None:
            queryset = self.get_queryset()
        
        # Get the pk from URL parameters
        pk = self.kwargs.get(self.pk_url_kwarg)
        
        if pk is None:
            raise AttributeError(
                "InvoiceDetailView must be called with an object pk in the URLconf."
            )
        
        # Try to get the invoice
        try:
            invoice = get_object_or_404(queryset, pk=pk)
        except Http404:
            # You could add custom logging or handling here
            raise Http404("Invoice not found or you don't have permission to view it.")
        
        return invoice

    def get_context_data(self, **kwargs):
        """
        Add additional context data to the template
        """
        context = super().get_context_data(**kwargs)
        invoice = self.object
        
        # Add calculated fields or additional data
        context['page_title'] = f"Invoice #{invoice.invoice_number}"
        context['breadcrumb'] = [
            {'name': 'Invoices', 'url': 'invoicelist'},
            {'name': f'Invoice #{invoice.invoice_number}', 'url': ''}
        ]
        
        # Add any additional context you might need
        context['company_name'] = "Business Solutions Ltd."
        context['company_address'] = "123 Business Street, Dar es Salaam, Tanzania"
        context['company_phone'] = "+255 123 456 789"
        context['company_email'] = "info@businesssolutions.tz"
        
        return context

    def dispatch(self, request, *args, **kwargs):
        """
        Additional pre-dispatch logic if needed
        """
        # You can add permission checks, logging, etc. here
        return super().dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        """
        Custom response handling if needed
        """
        # Check if it's a print request
        if self.request.GET.get('print') == 'true':
            context['print_mode'] = True
        
        # Check if it's a PDF export request
        if self.request.GET.get('format') == 'pdf':
            return self.generate_pdf_response(context)
        
        return super().render_to_response(context, **response_kwargs)

    def generate_pdf_response(self, context):
        """
        Method to generate PDF response (would need additional setup)
        """
        # This would require additional libraries like reportlab or weasyprint
        # For now, we'll just redirect to the HTML version
        from django.shortcuts import redirect
        return redirect('invoice_detail', pk=self.object.pk)

class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    template_name = 'invoice/invoice.html'
    form_class = InvoiceForm
    
    def get_success_url(self):
        return reverse('invoicelist')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = InvoiceItemFormSet(self.request.POST)
        else:
            context['formset'] = InvoiceItemFormSet()
        
        # Pass items for the dropdown
        context['items'] = Item.objects.all()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            # Save the invoice first
            self.object = form.save(commit=False)
            
            # Set any additional fields if needed
            # self.object.some_field = some_value
            
            self.object.save()
            
            # Now save the formset with the invoice instance
            formset.instance = self.object
            formset.save()
            
            return super().form_valid(form)
        else:
            print("Formset errors:", formset.errors)
            print("Formset non-form errors:", formset.non_form_errors())
            return self.form_invalid(form)

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        context = self.get_context_data()
        formset = context['formset']
        print("Formset errors:", formset.errors)
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

class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoice/invoice_form.html'  # Create this template
    
    def get_success_url(self):
        return reverse_lazy('invoice_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = InvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = InvoiceItemFormSet(instance=self.object)
        context['items'] = Item.objects.all()  # For the item dropdown
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            response = super().form_valid(form)
            formset.instance = self.object
            formset.save()
            
            # Update invoice totals
            self.object.save()
            
            return response
        else:
            return self.form_invalid(form)


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
