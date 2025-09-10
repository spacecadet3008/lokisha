from django.db import models
from django_extensions.db.fields import AutoSlugField
from .service import taxjar_service
from django.conf import settings

from store.models import Item
from accounts.models import Vendor, Customer

DELIVERY_CHOICES = [("P", "Pending"), ("S", "Successful")]


class Sale(models.Model):
    """
    Represents a sale transaction involving a customer.
    """

    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Sale Date"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.DO_NOTHING,
        db_column="customer"
    )
    sub_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )
    grand_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )
    tax_percentage = models.FloatField(default=0.0)
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=18
    )
    amount_change = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )

    class Meta:
        db_table = "sales"
        verbose_name = "Sale"
        verbose_name_plural = "Sales"

    def __str__(self):
        """
        Returns a string representation of the Sale instance.
        """
        return (
            f"Sale ID: {self.id} | "
            f"Grand Total: {self.grand_total} | "
            f"Date: {self.date_added}"
        )

    def sum_products(self):
        """
        Returns the total quantity of products in the sale.
        """
        return sum(detail.quantity for detail in self.saledetail_set.all())
    
    
    def calculate_tax_with_taxjar(self):
        """
        Calculate tax for this sale using TaxJar API
        """
        # Prepare order data for TaxJar
        order_data = {
            'from_country': settings.STORE_LOCATION['country'],
            'from_zip': settings.STORE_LOCATION['zip_code'],
            'from_state': settings.STORE_LOCATION['state'],
            'from_city': settings.STORE_LOCATION['city'],
            'from_street': settings.STORE_LOCATION['street'],
            'to_country': self.customer_country or 'US',
            'to_zip': self.customer_zip or settings.STORE_LOCATION['zip_code'],
            'to_state': self.customer_state,
            'to_city': self.customer_city,
            'amount': float(self.sub_total),
            'shipping': 0.0,
            'line_items': []
        }
        
        # Add line items
        for detail in self.saledetail_set.all():
            order_data['line_items'].append({
                'id': str(detail.item.id),
                'quantity': detail.quantity,
                'product_tax_code': self.get_tax_code_for_category(detail.item.category.name),
                'unit_price': float(detail.price),
                'discount': 0.0
            })
        
        # Calculate tax using TaxJar
        tax_result = taxjar_service.calculate_tax_for_order(order_data)
        
        return tax_result['amount_to_collect'], tax_result['rate'] * 100, {
            'taxjar_response': tax_result
        }
    
    def get_tax_code_for_category(self, category_name):
        """
        Map category names to TaxJar product tax codes
        """
        tax_codes = {
            'Clothing': '31000',
            'Electronics': '31000',
            'Food': '40030',
            'Books': '81100',
            'Software': '51010',
        }
        return tax_codes.get(category_name, '31000')
    
    def save(self, *args, **kwargs):
        """
        Override save to calculate tax using TaxJar
        """
        if not self.tax_data and self.saledetail_set.exists():
            try:
                tax_amount, tax_percentage, tax_breakdown = self.calculate_tax_with_taxjar()
                self.tax_amount = tax_amount
                self.tax_percentage = tax_percentage
                self.tax_data = tax_breakdown
                
                # Recalculate grand total
                self.grand_total = self.sub_total + self.tax_amount
                
                # Recalculate change
                self.amount_change = max(0, self.amount_paid - self.grand_total)
            except Exception as e:
                logger.error(f"Error calculating tax with TaxJar: {str(e)}")
                # Fallback to simple calculation
                fallback_rate = taxjar_service.get_fallback_rate()
                self.tax_amount = float(self.sub_total) * (fallback_rate / 100)
                self.tax_percentage = fallback_rate
                self.grand_total = self.sub_total + self.tax_amount
                self.amount_change = max(0, self.amount_paid - self.grand_total)
                self.tax_data = {'source': 'fallback', 'rate': fallback_rate}
        
        super().save(*args, **kwargs)


class SaleDetail(models.Model):
    """
    Represents details of a specific sale, including item and quantity.
    """

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        db_column="sale",
        related_name="saledetail_set"
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.DO_NOTHING,
        db_column="item"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    quantity = models.PositiveIntegerField()
    total_detail = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "sale_details"
        verbose_name = "Sale Detail"
        verbose_name_plural = "Sale Details"

    def __str__(self):
        """
        Returns a string representation of the SaleDetail instance.
        """
        return (
            f"Detail ID: {self.id} | "
            f"Sale ID: {self.sale.id} | "
            f"Quantity: {self.quantity}"
        )
    


class Purchase(models.Model):
    """
    Represents a purchase of an item,
    including vendor details and delivery status.
    """

    slug = AutoSlugField(unique=True, populate_from="vendor")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    description = models.TextField(max_length=300, blank=True, null=True)
    vendor = models.ForeignKey(
        Vendor, related_name="purchases", on_delete=models.CASCADE
    )
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Delivery Date"
    )
    quantity = models.PositiveIntegerField(default=0)
    delivery_status = models.CharField(
        choices=DELIVERY_CHOICES,
        max_length=1,
        default="P",
        verbose_name="Delivery Status",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        verbose_name="Price per item (Tsh)",
    )
    total_value = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """
        Calculates the total value before saving the Purchase instance.
        """
        self.total_value = self.price * self.quantity
        super().save(*args, **kwargs)
        # Update the item quantity
        self.item.quantity += self.quantity
        self.item.save()

    def __str__(self):
        """
        Returns a string representation of the Purchase instance.
        """
        return str(self.item.name)

    class Meta:
        ordering = ["order_date"]
