import django_tables2 as tables
from .models import Invoice
import django_tables2 as tables
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

class InvoiceTable(tables.Table):
    """
    Table representation for the Invoice model.
    """

    class Meta:
        model = Invoice
        template_name = "django_tables2/semantic.html"
        fields = (
            'date', 'customer_name', 'contact_number', 'item',
            'price_per_item', 'quantity', 'total','is_proforma','status'
        )
        order_by = 'date'

class ProformaTable(tables.Table):
    """Table for displaying proforma invoices"""
    
    invoice_number = tables.Column(
        verbose_name='Proforma #',
        attrs={'td': {'class': 'fw-bold'}}
    )
    
    date = tables.DateTimeColumn(
        format='M d, Y',
        verbose_name='Date'
    )
    
    customer_name = tables.Column(
        accessor='customer_name.get_full_name',
        verbose_name='Customer'
    )
    
    total = tables.Column(
        verbose_name='Total (Tsh)',
        attrs={'td': {'class': 'text-end'}}
    )
    
    grand_total = tables.Column(
        verbose_name='Grand Total (Tsh)',
        attrs={'td': {'class': 'text-end fw-bold'}}
    )
    
    status = tables.Column(
        verbose_name='Status',
        attrs={'td': {'class': 'text-center'}}
    )
    
    actions = tables.Column(
        empty_values=(),
        orderable=False,
        verbose_name='Actions',
        attrs={
            'th': {'class': 'text-center', 'style': 'width: 150px;'},
            'td': {'class': 'text-center'}
        }
    )
    
    class Meta:
        model = Invoice
        fields = ('invoice_number', 'date', 'customer_name', 'contact_number', 'total', 'shipping', 'grand_total', 'status')
        template_name = 'django_tables2/bootstrap5.html'
        attrs = {
            'class': 'table table-hover table-striped',
            'thead': {'class': 'table-light'}
        }
    
    def render_invoice_number(self, value, record):
        if record.is_proforma and value.startswith('P'):
            return format_html('<strong>P{}</strong>', value[1:])
        return value
    
    def render_total(self, value):
        return format_html('Tsh {:,.2f}', value) if value else 'Tsh 0.00'
    
    def render_grand_total(self, value):
        return format_html('<span class="text-success">Tsh {:,.2f}</span>', value) if value else 'Tsh 0.00'
    
    def render_status(self, value, record):
        status_classes = {
            'draft': 'badge bg-secondary',
            'sent': 'badge bg-info',
            'accepted': 'badge bg-success',
            'cancelled': 'badge bg-danger'
        }
        return format_html(
            '<span class="{}">{}</span>',
            status_classes.get(value, 'badge bg-secondary'),
            value.title()
        )
    
    def render_actions(self, record):
        actions = []
        
        # View action
        actions.append(format_html(
            '<a href="{}" class="btn btn-sm btn-info" title="View">'
            '<i class="fas fa-eye"></i></a>',
            reverse('proforma_detail', kwargs={'pk': record.pk})
        ))
        
        # Edit action
        actions.append(format_html(
            '<a href="{}" class="btn btn-sm btn-primary" title="Edit">'
            '<i class="fas fa-edit"></i></a>',
            reverse('proforma_edit', kwargs={'pk': record.pk})
        ))
        
        # Convert to invoice action (only for draft/sent proformas)
        if record.status in ['draft', 'sent'] and not record.converted_to_invoice:
            actions.append(format_html(
                '<a href="{}" class="btn btn-sm btn-success" title="Convert to Invoice">'
                '<i class="fas fa-exchange-alt"></i></a>',
                reverse('proforma_convert', kwargs={'pk': record.pk})
            ))
        
        # Delete action
        actions.append(format_html(
            '<a href="{}" class="btn btn-sm btn-danger" title="Delete" '
            'onclick="return confirm(\'Are you sure you want to delete this proforma invoice?\')">'
            '<i class="fas fa-trash"></i></a>',
            reverse('proforma_delete', kwargs={'pk': record.pk})
        ))
        
        return mark_safe(' '.join(actions))