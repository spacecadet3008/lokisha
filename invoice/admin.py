from django.contrib import admin
from .models import Invoice, InvoiceItem,DeliveryItem,Delivery

# Import your models


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ['total_price']
    fields = ['item', 'quantity', 'price_per_item', 'total_price']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item')


class DeliveryItemInline(admin.TabularInline):
    model = DeliveryItem
    extra = 1
    fields = ['item', 'quantity', 'price_per_item', 'total_price']
    readonly_fields = ['total_price']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'status','is_proforma','customer_name', 'date', 'total', 'shipping', 'grand_total']
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
@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['delivery_number', 'customer_name', 'date', 'status', 'converted_to_invoice']
    list_filter = ['status', 'date']
    search_fields = ['delivery_number', 'customer_name__name', 'contact_number']
    inlines = [DeliveryItemInline]
    readonly_fields = ['delivery_number']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['delivery_number', 'date', 'customer_name', 'contact_number']
        }),
        ('Delivery Details', {
            'fields': ['shipping_address', 'status', 'notes', 'converted_to_invoice']
        }),
    ]

@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):
    list_display = ['delivery', 'item', 'quantity', 'price_per_item', 'total_price']
    list_filter = ['delivery__status']
    search_fields = ['delivery__delivery_number', 'item__name']

# Optional: Custom admin site header and title
admin.site.site_header = 'Business Management System Administration'
admin.site.site_title = 'Business Management System'
admin.site.index_title = 'System Administration'