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
    DetailView, CreateView, UpdateView, DeleteView,View,ListView
)
from django.views.generic.edit import FormView

# Third-party packages
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

# Local app imports
from .models import Invoice,Delivery
from accounts.models import Customer
from store.models import Item
from .tables import InvoiceTable,ProformaTable
from .forms import InvoiceForm,InvoiceItemFormSet,DeliveryForm,DeliveryItemFormSet
from django.shortcuts import get_object_or_404
from django.http import Http404


class InvoiceListView(LoginRequiredMixin, ExportMixin, SingleTableView):
    """View for listing regular invoices (non-proforma)"""
    model = Invoice
    table_class = InvoiceTable
    template_name = 'invoice/invoicelist.html'
    context_object_name = 'invoices'
    paginate_by = 10
    table_pagination = False
    export_name = 'invoices'
    
    def get_queryset(self):
        """Return only regular invoices (non-proforma) with optional filtering"""
        queryset = Invoice.objects.filter(is_proforma=False).select_related(
            'customer_name'
        ).prefetch_related(
            'items'
        ).order_by('-date')
        
        # Search filter
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search_query) |
                Q(customer_name__first_name__icontains=search_query) |
                Q(customer_name__last_name__icontains=search_query) |
                Q(contact_number__icontains=search_query)
            )
        
        # Status filter
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Invoices'
        context['breadcrumb'] = [
            {'name': 'Dashboard', 'url': reverse_lazy('dashboard')},
            {'name': 'Invoices', 'url': ''}
        ]
        
        # Add status filter options
        context['status_choices'] = [
            ('', 'All Statuses'),
            ('draft', 'Draft'),
            ('sent', 'Sent'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled')
        ]
        
        # Pass current filter values
        context['current_search'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        
        return context

class ProformaListView(LoginRequiredMixin, ExportMixin, SingleTableView):
    """View for listing proforma invoices with table export functionality."""
    model = Invoice
    table_class = ProformaTable
    template_name = 'invoice/proforma_list.html'
    context_object_name = 'proformas'
    paginate_by = 10
    table_pagination = False
    export_name = 'proforma_invoices'
    
    def get_queryset(self):
        """Return only proforma invoices with optional filtering"""
        queryset = Invoice.objects.filter(is_proforma=True).select_related(
            'customer_name'
        ).prefetch_related(
            'items'
        ).order_by('-date')
        
        # Search filter
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search_query) |
                Q(customer_name__first_name__icontains=search_query) |
                Q(customer_name__last_name__icontains=search_query) |
                Q(contact_number__icontains=search_query)
            )
        
        # Status filter
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Proforma Invoices'
        context['breadcrumb'] = [
            {'name': 'Dashboard', 'url': reverse_lazy('dashboard')},
            {'name': 'Proforma Invoices', 'url': ''}
        ]
        
        # Add status filter options
        context['status_choices'] = [
            ('', 'All Statuses'),
            ('draft', 'Draft'),
            ('sent', 'Sent'),
            ('accepted', 'Accepted'),
            ('cancelled', 'Cancelled')
        ]
        
        # Pass current filter values
        context['current_search'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        
        return context


# views.py
class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoice/invoicedetail.html'
    context_object_name = 'invoice'
    pk_url_kwarg = 'pk'

    def get_template_names(self):
        # Use print template if print parameter is present
        if self.request.GET.get('print') == 'true':
            return ['invoice/invoice_print.html']
        return ['invoice/invoicedetail.html']
    
    def get_queryset(self):
        """
        Optimize database queries by prefetching related data
        """
        return Invoice.objects.prefetch_related(
            'items__item'
        ).select_related(
            'customer_name'
        )

    def get_context_data(self, **kwargs):
        """
        Add additional context data to the template
        """
        context = super().get_context_data(**kwargs)
        invoice = self.object
        
        if invoice.is_proforma:
            context['page_title'] = f"Proforma Invoice #{invoice.invoice_number}"
            context['breadcrumb'] = [
                {'name': 'Proforma Invoices', 'url': 'proforma_list'},
                {'name': f'Proforma #{invoice.invoice_number}', 'url': ''}
            ]
        else:
            context['page_title'] = f"Invoice #{invoice.invoice_number}"
            context['breadcrumb'] = [
                {'name': 'Invoices', 'url': 'invoicelist'},
                {'name': f'Invoice #{invoice.invoice_number}', 'url': ''}
            ]
        
        # Add company information
        context['company_name'] = "Business Solutions Ltd."
        context['company_address'] = "123 Business Street, Dar es Salaam, Tanzania"
        context['company_phone'] = "+255 123 456 789"
        context['company_email'] = "info@businesssolutions.tz"
        
        # Add source proforma info if this invoice was converted
        if not invoice.is_proforma and hasattr(invoice, 'proforma_source'):
            context['proforma_source'] = invoice.proforma_source
        
        return context

class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    template_name = 'invoice/invoice.html'
    form_class = InvoiceForm
    
    def get_initial(self):
        initial = super().get_initial()
        # Set default as proforma if requested
        if self.request.GET.get('type') == 'proforma':
            initial['is_proforma'] = True
        return initial
    
    def get_success_url(self):
        if self.object.is_proforma:
            print(f"Redirecting to proforma detail: {self.object.pk}")
            return reverse('proforma_detail', kwargs={'pk': self.object.pk})
        else:
            print(f"Redirecting to invoice detail: {self.object.pk}")
            return reverse('invoice-detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = InvoiceItemFormSet(self.request.POST)
        else:
            context['formset'] = InvoiceItemFormSet()
        
        # Pass items for the dropdown
        context['items'] = Item.objects.all()
        
        # Check if creating a proforma
        if self.request.GET.get('type') == 'proforma':
            context['is_proforma'] = True
            context['page_title'] = 'Create Proforma Invoice'
        
        return context

    def form_valid(self, form):  # This should be indented properly
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            # Save the invoice first
            self.object = form.save(commit=False)
            
            # Debug print
            print(f"Creating invoice - is_proforma: {self.object.is_proforma}")
            # Ensure it's marked as proforma if coming from proforma create URL
            if 'proforma' in self.request.path or self.request.GET.get('type') == 'proforma':
                self.object.is_proforma = True
            
            # Set initial status based on button clicked
            if 'save_draft' in self.request.POST:
                self.object.status = 'draft'
            elif 'save_send' in self.request.POST:
                self.object.status = 'sent'
            else:
                self.object.status = 'draft'  # Default to draft
            
            self.object.save()
            
            # Now save the formset with the invoice instance
            formset.instance = self.object
            formset.save()
            
            return super().form_valid(form)
        else:
            print("Formset errors:", formset.errors)
            return self.form_invalid(form)

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
        return reverse_lazy('invoice-detail', kwargs={'pk': self.object.pk})

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


class ProformaConvertView(LoginRequiredMixin, View):
    """View to convert a proforma invoice to a regular invoice"""
    
    def post(self, request, *args, **kwargs):
        proforma = get_object_or_404(Invoice, pk=kwargs['pk'], is_proforma=True)
        
        if proforma.converted_to_invoice:
            messages.warning(request, 'This proforma has already been converted.')
            return redirect('proforma_detail', pk=proforma.pk)
        
        invoice = proforma.convert_to_invoice()
        messages.success(request, f'Proforma converted to invoice #{invoice.invoice_number}')
        
        return redirect('invoice_detail', pk=invoice.pk)



""" Delivery Invoice Views """

# views.py
class DeliveryListView(LoginRequiredMixin, ListView):
    model = Delivery
    template_name = 'invoice/delivery_list.html'
    context_object_name = 'deliveries'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Delivery.objects.select_related('customer_name').prefetch_related('items').order_by('-date')
        
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(delivery_number__icontains=search_query) |
                Q(customer_name__first_name__icontains=search_query) |
                Q(customer_name__last_name__icontains=search_query)
            )
            
        return queryset


class DeliveryCreateView(LoginRequiredMixin, CreateView):
    model = Delivery
    form_class = DeliveryForm
    template_name = 'invoice/delivery_form.html'
    
    def get_success_url(self):
        return reverse('delivery_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = DeliveryItemFormSet(self.request.POST)
        else:
            context['formset'] = DeliveryItemFormSet()
        context['items'] = Item.objects.all()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return super().form_valid(form)
        return self.form_invalid(form)


class DeliveryDetailView(LoginRequiredMixin, DetailView):
    model = Delivery
    template_name = 'invoice/delivery_detail.html'
    context_object_name = 'delivery'

    def get_template_names(self):
        # Use print template if print parameter is present
        if self.request.GET.get('print') == 'true':
            return ['invoice/delivery_print.html']
        return ['invoice/delivery_detail.html']


class DeliveryUpdateView(LoginRequiredMixin, UpdateView):
    model = Delivery
    form_class = DeliveryForm
    template_name = 'invoice/delivery_form.html'
    
    def get_success_url(self):
        return reverse('delivery_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = DeliveryItemFormSet(self.request.POST, instance=self.object)
        else:
            # Pre-populate the formset with existing items
            context['formset'] = DeliveryItemFormSet(instance=self.object)
        context['items'] = Item.objects.all()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return super().form_valid(form)
        return self.form_invalid(form)


class DeliveryConvertView(LoginRequiredMixin, View):
    """Convert delivery to invoice"""
    
    def post(self, request, *args, **kwargs):
        delivery = get_object_or_404(Delivery, pk=kwargs['pk'])
        
        if delivery.delivery_source:
            messages.warning(request, 'This delivery has already been converted to an invoice.')
            return redirect('delivery_detail', pk=delivery.pk)
        
        invoice = delivery.convert_to_invoice()
        messages.success(request, f'Delivery converted to invoice #{invoice.invoice_number}')
        
        return redirect('invoice_detail', pk=invoice.pk)

from .utils import generate_pdf_response

def generate_invoice_pdf(request, pk):
    """Generate PDF for invoice or proforma"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    context = {
        'invoice': invoice,
    }
    
    filename = f"{'proforma' if invoice.is_proforma else 'invoice'}_{invoice.invoice_number}.pdf"
    return generate_pdf_response('invoice/invoice_pdf.html', context, filename)

def generate_delivery_pdf(request, pk):
    """Generate PDF for delivery"""
    delivery = get_object_or_404(Delivery, pk=pk)
    
    # Calculate total
    delivery_total = sum(item.total_price for item in delivery.items.all())
    
    context = {
        'delivery': delivery,
        'delivery_total': delivery_total,
    }
    
    filename = f"delivery_{delivery.delivery_number}.pdf"
    return generate_pdf_response('invoice/delivery_pdf.html', context, filename)