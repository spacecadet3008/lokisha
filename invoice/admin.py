from django.contrib import admin
from .models import Invoice, InvoiceItem

# Import your models


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ['total_price']
    fields = ['item', 'quantity', 'price_per_item', 'total_price']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer_name', 'date', 'total', 'shipping', 'grand_total']
    list_filter = ['date', 'customer_name']
    search_fields = ['invoice_number', 'customer_name__first_name', 'customer_name__last_name']
    readonly_fields = ['invoice_number', 'total', 'grand_total', 'slug']
    date_hierarchy = 'date'
    inlines = [InvoiceItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('invoice_number', 'date', 'slug')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'contact_number')
        }),
        ('Financial Information', {
            'fields': ('shipping', 'total', 'grand_total')
        }),
    )



@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'item', 'quantity', 'price_per_item', 'total_price']
    list_filter = ['invoice__date', 'item']
    search_fields = ['invoice__invoice_number', 'item__name']
    readonly_fields = ['total_price']
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice',)
        }),
        ('Item Information', {
            'fields': ('item', 'quantity', 'price_per_item', 'total_price')
        }),
    )

# Optional: Custom admin site header and title
admin.site.site_header = 'Business Management System Administration'
admin.site.site_title = 'Business Management System'
admin.site.index_title = 'System Administration'