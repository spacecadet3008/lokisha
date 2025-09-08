from django.db import models
from django.utils import timezone
from django_extensions.db.fields import AutoSlugField
from django.db.models.signals import pre_save,post_save,post_delete
from django.dispatch import receiver

from store.models import Item
from accounts.models import Customer

# models.py
class Invoice(models.Model):
    """
    Represents an invoice or proforma invoice header.
    """
    INVOICE_TYPE_CHOICES = [
        ('invoice', 'Invoice'),
        ('proforma', 'Proforma Invoice'),
    ]
    
    slug = AutoSlugField(unique=True, populate_from='get_invoice_slug')
    date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Invoice Date'
    )
    delivery_source = models.OneToOneField(
        'Delivery',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='delively_invoice'
    )
    invoice_number = models.CharField(max_length=7, unique=True, blank=True, null=True, editable=False)
    customer_name = models.ForeignKey(Customer, related_name='invoices', verbose_name='Customer', on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=13)
    shipping = models.FloatField(verbose_name='Shipping and Handling', blank=True, default=0.0)
    total = models.FloatField(verbose_name='Total Amount (Tsh)', editable=False, default=0.0)
    grand_total = models.FloatField(verbose_name='Grand Total (Tsh)', editable=False, default=0.0)
    is_proforma = models.BooleanField(default=False, verbose_name='Proforma Invoice')
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('sent', 'Sent'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled')
        ],
        default='draft'
    )
    converted_to_invoice = models.OneToOneField(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='proforma_source'
    )

    def get_invoice_slug(self):
        return f"inv-{self.invoice_number}"

    def save(self, *args, **kwargs):
        """
        Update totals before saving.
        """
        # Calculate totals from invoice items - ALWAYS calculate, not just when pk exists
        if self.pk:  # We have items only if the invoice exists
            items_total = sum(item.total_price for item in self.items.all())
            self.total = round(items_total, 2)
            self.grand_total = round(self.total + self.shipping, 2)
        else:
            # For new invoices, set defaults
            self.total = 0.0
            self.grand_total = 0.0
        
        if not self.invoice_number:
            prefix = "P" if self.is_proforma else "I"
            self.invoice_number = self.get_next_invoice_number(prefix)
            
        super().save(*args, **kwargs)

    def convert_to_invoice(self):
        """Convert proforma invoice to a regular invoice"""
        if not self.is_proforma:
            return self
        
        # Create a new invoice based on this proforma
        invoice = Invoice.objects.create(
            customer_name=self.customer_name,
            contact_number=self.contact_number,
            shipping=self.shipping,
            is_proforma=False,
            status='draft'
        )
        
        # Copy all items
        for item in self.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                item=item.item,
                quantity=item.quantity,
                price_per_item=item.price_per_item
            )
        
        # Save to calculate totals
        invoice.save()
        
        # Mark this proforma as converted
        self.converted_to_invoice = invoice
        self.status = 'paid'  # Or whatever status makes sense
        self.save()
        
        return invoice

    def __str__(self):
        prefix = "Proforma " if self.is_proforma else "Invoice "
        return f"{prefix}#{self.invoice_number} - {self.customer_name}"

    @classmethod
    def get_next_invoice_number(cls, prefix="I"):
        last_invoice = cls.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('invoice_number').last()
        
        if not last_invoice:
            return f"{prefix}0001"
        
        try:
            last_number = int(last_invoice.invoice_number[1:])
            next_number = last_number + 1
            if next_number > 9999:
                next_number = 1
            return f"{prefix}{next_number:04d}"
        except (ValueError, TypeError):
            return f"{prefix}0001"


class InvoiceItem(models.Model):
    """
    Represents an item within an invoice.
    """
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, related_name='invoice_items', verbose_name='Product', on_delete=models.CASCADE)
    quantity = models.FloatField(default=1)
    price_per_item = models.FloatField(verbose_name='Price Per Item (Tsh)',default=0.0)
    total_price = models.FloatField(verbose_name='Total Price (Tsh)', editable=False)

    def save(self, *args, **kwargs):
        """
        Calculate total price before saving.
        """
        self.total_price = round(self.quantity * self.price_per_item, 2)
        super().save(*args, **kwargs)
        
        # Update the parent invoice totals
        if self.invoice:
            self.invoice.save()

    def __str__(self):
        return f"{self.quantity} x {self.item.name} - Tsh {self.total_price}"

    class Meta:
        ordering = ['id']


class Delivery(models.Model):
    """Represents a delivery note that can be converted to an invoice"""
    DELIVERY_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('preparing', 'Preparing'),
        ('dispatched', 'Dispatched'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]
    
    delivery_number = models.CharField(max_length=7, unique=True, blank=True, null=True, editable=False)
    date = models.DateTimeField(default=timezone.now, verbose_name='Delivery Date')
    customer_name = models.ForeignKey(Customer, related_name='deliveries', on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=13)
    shipping_address = models.TextField(verbose_name='Delivery Address')
    status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, verbose_name='Delivery Notes')
    converted_to_invoice = models.OneToOneField(
        'Invoice',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='delivery_invoice'
    )
    
    def save(self, *args, **kwargs):
        if not self.delivery_number:
            self.delivery_number = self.get_next_delivery_number()
        super().save(*args, **kwargs)
    
    def convert_to_invoice(self):
        """Convert delivery to invoice"""
        if self.converted_to_invoice:
            return self.converted_to_invoice
        
        invoice = Invoice.objects.create(
            customer_name=self.customer_name,
            contact_number=self.contact_number,
            shipping=0.0,
            is_proforma=False,
            status='draft',
            # Set the reverse relationship
            delivery_source=self  # This will set the OneToOneField from Invoice side
        )
        
        # Copy delivery items to invoice
        for delivery_item in self.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                item=delivery_item.item,
                quantity=delivery_item.quantity,
                price_per_item=delivery_item.price_per_item
            )
        
        invoice.save()
        self.converted_to_invoice = invoice
        self.status = 'delivered'
        self.save()
        
        return invoice
    
    @classmethod
    def get_next_delivery_number(cls):
        last_delivery = cls.objects.order_by('delivery_number').last()
        if not last_delivery:
            return "DL00001"
        try:
            last_number = int(last_delivery.delivery_number[2:])
            next_number = last_number + 1
            return f"DL{next_number:05d}"
        except (ValueError, TypeError):
            return "DL00001"
    
    def __str__(self):
        return f"Delivery #{self.delivery_number} - {self.customer_name}"


class DeliveryItem(models.Model):
    """Items within a delivery"""
    delivery = models.ForeignKey(Delivery, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, related_name='delivery_items', on_delete=models.CASCADE)
    quantity = models.FloatField(default=1)
    price_per_item = models.FloatField(verbose_name='Price Per Item (Tsh)', default=0.0)
    total_price = models.FloatField(verbose_name='Total Price (Tsh)', editable=False)
    
    def save(self, *args, **kwargs):
        self.total_price = round(self.quantity * self.price_per_item, 2)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quantity} x {self.item.name} - Delivery"

@receiver(post_save, sender=InvoiceItem)
@receiver(post_delete, sender=InvoiceItem)
def update_invoice_totals(sender, instance, **kwargs):
    """
    Update invoice totals when items are saved or deleted.
    """
    invoice = instance.invoice
    if invoice and invoice.pk:
        items_total = sum(item.total_price for item in invoice.items.all())
        invoice.total = round(items_total, 2)
        invoice.grand_total = round(invoice.total + invoice.shipping, 2)
        # Use update() to avoid recursive save
        Invoice.objects.filter(pk=invoice.pk).update(
            total=invoice.total,
            grand_total=invoice.grand_total
        )

@receiver(pre_save, sender=Invoice)
def set_invoice_number(sender, instance, **kwargs):
    """
    Set invoice number before saving if it doesn't exist.
    """
    if not instance.invoice_number:
        prefix = "P" if instance.is_proforma else "I"
        instance.invoice_number = Invoice.get_next_invoice_number(prefix)


