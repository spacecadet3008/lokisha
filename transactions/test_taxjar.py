import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from .service import TaxjarService

def test_taxjar():
    service = TaxjarService
    
    # Test getting a tax rate
    rate = service.get_tax_rate('10001') # New York zip code
    print(f"Tax rate for 10001: {rate}%")
    
    # Test calculating tax for an order
    order_data = {
        'from_country': 'US',
        'from_zip': '10001',
        'from_state': 'NY',
        'from_city': 'New York',
        'from_street': '123 Main St',
        'to_country': 'US',
        'to_zip': '10001',
        'to_state': 'NY',
        'to_city': 'New York',
        'amount': 100.0,
        'shipping': 0.0,
        'line_items': [
            {
                'id': '1',
                'quantity': 2,
                'product_tax_code': '31000',
                'unit_price': 50.0,
                'discount': 0.0
            }
        ]
    }
    
    tax_result = service.calculate_tax_for_order(order_data)
    print(f"Tax amount: ${tax_result['amount_to_collect']}")
    print(f"Tax rate: {tax_result['rate'] * 100}%")

if __name__ == '__main__':
    test_taxjar()