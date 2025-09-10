import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class TaxjarService:
    def __init__(self):
        self.api_key = getattr(settings,'TAXJAR_API_KEY',None) # tra key
        self.api_url = getattr(settings,'TAXJAR_API_URL','https://api.taxjar.com') # link of api

        self.fallback_rates = getattr(settings,'FALLBACK_TAX_PAYER',{})

        if not self.api_key:
            logger("TAXJAR_API_KEY not found in settings")
        
    def make_request(self,endpoint,payload=None,method='GET'):
        if not self.api_key:
            return None
        
        url = f"{self.api_url}/{endpoint}"

        headers = {
            'Authorization': f'Bearer{self.api_key}',
            'content_type':'application/json'
        }

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=payload, timeout=10)
            else:
                response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"TaxJar API request failed: {str(e)}")
            return None
    
    def get_tax_rate(self, zip_code, country='US', city=None, state=None):
        """
        Get tax rate for a location using TaxJar API
        """
        # Try to get rate from TaxJar API
        params = {
            'country': country,
            'zip': zip_code
        }
        if city:
            params['city'] = city
        if state:
            params['state'] = state
            
        result = self._make_request('v2/rates/' + zip_code, params, 'GET')
        
        if result and 'rate' in result:
            rate_data = result['rate']
            combined_rate = float(rate_data['combined_rate']) * 100  # Convert to percentage
            return combined_rate
        
        # Fallback if API fails
        logger.warning("TaxJar API unavailable, using fallback rate")
        return self.get_fallback_rate()
    
    def calculate_tax_for_order(self, order_data):
        """
        Calculate tax for an order using TaxJar API
        """
        result = self._make_request('v2/taxes', order_data, 'POST')
        
        if result and 'tax' in result:
            tax_data = result['tax']
            return {
                'amount_to_collect': float(tax_data['amount_to_collect']),
                'rate': float(tax_data['rate']),
                'has_nexus': tax_data['has_nexus'],
                'freight_taxable': tax_data['freight_taxable'],
                'tax_source': tax_data['tax_source'],
                'breakdown': tax_data.get('breakdown')
            }
        
        # Fallback if API fails
        logger.warning("TaxJar API unavailable, using fallback calculation")
        return self.calculate_tax_fallback(order_data)
    
    def get_fallback_rate(self):
        """
        Get fallback tax rate
        """
        return self.fallback_rates.get('default', 8.0)
    
    def calculate_tax_fallback(self, order_data):
        """
        Fallback tax calculation if TaxJar is unavailable
        """
        amount = order_data.get('amount', 0)
        fallback_rate = self.get_fallback_rate()
        tax_amount = amount * (fallback_rate / 100)
        
        return {
            'amount_to_collect': tax_amount,
            'rate': fallback_rate / 100,
            'has_nexus': True,
            'freight_taxable': False,
            'tax_source': "fallback",
            'breakdown': None
        }

# Create a singleton instance
taxjar_service = TaxjarService