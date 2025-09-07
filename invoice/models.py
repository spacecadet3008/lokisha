from django.db import models
from django.utils import timezone
from django_extensions.db.fields import AutoSlugField
from django.db.models.signals import pre_save
from django.dispatch import receiver

from store.models import Item
from accounts.models import Customer

# models.py
class Invoice(models.Model):
    """
    Represents an invoice header.
    """
    slug = AutoSlugField(unique=True, populate_from='get_invoice_slug')
    date = models.DateTimeField(
        default=timezone.now,  # Change from auto_now to default
        verbose_name='Invoice Date'
    )
    invoice_number = models.CharField(max_length=7, unique=True, blank=True, null=True, editable=False)
    customer_name = models.ForeignKey(Customer, related_name='invoices', verbose_name='Customer', on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=13)
    shipping = models.FloatField(verbose_name='Shipping and Handling', blank=True, default=0.0)
    total = models.FloatField(verbose_name='Total Amount (Tsh)', editable=False, default=0.0)
    grand_total = models.FloatField(verbose_name='Grand Total (Tsh)', editable=False, default=0.0)

    def get_invoice_slug(self):
        return f"inv-{self.invoice_number}"

    def save(self, *args, **kwargs):
        """
        Update totals before saving.
        """
        # Calculate totals from invoice items
        if self.pk:  # Only if invoice already exists
            items_total = sum(item.total_price for item in self.items.all())
            self.total = round(items_total, 2)
            self.grand_total = round(self.total + self.shipping, 2)
        
        if not self.invoice_number:
            self.invoice_number = self.get_next_invoice_number()
            
        super().save(*args, **kwargs)

    # ... rest of the model

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.customer_name}"

    @classmethod
    def get_next_invoice_number(cls):
        last_invoice = cls.objects.order_by('invoice_number').last()
        if not last_invoice:
            return "0001"
        try:
            last_number = int(last_invoice.invoice_number)
            next_number = last_number + 1
            if next_number > 9999:
                next_number = 1
            return f"{next_number:04d}"
        except (ValueError, TypeError):
            return "0001"


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