from django import forms
from .models import Invoice
from store.models import Item
from accounts.models import Customer

class InvoiceForm(forms.ModelForm):
    # Add these fields to handle the autocomplete inputs
    customer_search = forms.CharField(required=False, widget=forms.HiddenInput())
    item_search = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = Invoice
        fields = [
            'customer_name', 'contact_number', 'item',
            'price_per_item', 'quantity', 'shipping'
        ]
        widgets = {
            'customer_name': forms.HiddenInput(),
            'item': forms.HiddenInput(),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact number...'
            }),
            'price_per_item': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                  # Make it readonly since it's auto-populated
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'shipping': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }
    
    def clean_item(self):
        item_id = self.cleaned_data.get('item')
        if item_id:
            try:
                return Item.objects.get(id=item_id)
            except Item.DoesNotExist:
                raise forms.ValidationError("Selected item does not exist.")
        return None