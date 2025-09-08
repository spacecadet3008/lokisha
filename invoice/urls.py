# Django core imports
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

# Local app imports
from .views import (
    ProformaListView,
    InvoiceCreateView,
    InvoiceDetailView, 
    InvoiceUpdateView, 
    InvoiceDeleteView, 
    InvoiceListView,
    ProformaConvertView,
    generate_invoice_pdf, 
    generate_delivery_pdf,
    autocomplete_customers, 
    autocomplete_items,
    DeliveryListView,
    DeliveryCreateView,
    DeliveryDetailView,
    DeliveryUpdateView,
    DeliveryConvertView
    
)

# URL patterns
urlpatterns = [
    # Regular invoices
    path('invoices/', InvoiceListView.as_view(), name='invoicelist'),
    path('invoice/create/', InvoiceCreateView.as_view(), name='invoice-create'),
    path('invoice/<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoice/<int:pk>/update/', InvoiceUpdateView.as_view(), name='invoice-update'),
    path('invoice/<int:pk>/delete/', InvoiceDeleteView.as_view(), name='invoice-delete'),
    
    # Proforma invoices
    path('proformas/', ProformaListView.as_view(), name='proforma_list'),
    path('proforma/create/', InvoiceCreateView.as_view(), name='proforma_create'),
    path('proforma/<int:pk>/', InvoiceDetailView.as_view(), name='proforma_detail'),
    path('proforma/<int:pk>/edit/', InvoiceUpdateView.as_view(), name='proforma_edit'),
    path('proforma/<int:pk>/convert/', ProformaConvertView.as_view(), name='proforma_convert'),
    path('proforma/<int:pk>/delete/', InvoiceDeleteView.as_view(), name='proforma_delete'),

    # Delivery 
    path('deliveries/', DeliveryListView.as_view(), name='delivery_list'),
    path('delivery/create/', DeliveryCreateView.as_view(), name='delivery_create'),
    path('delivery/<int:pk>/', DeliveryDetailView.as_view(), name='delivery_detail'),
    path('delivery/<int:pk>/edit/', DeliveryUpdateView.as_view(), name='delivery_edit'),
    path('delivery/<int:pk>/convert/', DeliveryConvertView.as_view(), name='delivery_convert'),
    
    # Autocomplete
    path('autocomplete/customers/', autocomplete_customers, name='autocomplete_customers'),
    path('autocomplete/items/', autocomplete_items, name='autocomplete_items'),


    # pdf convertor 
    path('invoice/<int:pk>/pdf/', generate_invoice_pdf, name='invoice_pdf'),
    path('proforma/<int:pk>/pdf/', generate_invoice_pdf, name='proforma_pdf'),
    path('delivery/<int:pk>/pdf/', generate_delivery_pdf, name='delivery_pdf'),
]

# Static media files configuration for development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
