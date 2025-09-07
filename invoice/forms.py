from django import forms
from .models import Invoice,InvoiceItem
from store.models import Item
from accounts.models import Customer

# forms.py
from django.forms import inlineformset_factory

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer_name', 'contact_number', 'shipping']
        widgets = {
            'customer_name': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%'
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact number...'
            }),
            'shipping': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['item', 'quantity', 'price_per_item']
        widgets = {
            'item': forms.HiddenInput(),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'step': '0.01',
                'min': '0.01'
            }),
            'price_per_item': forms.NumberInput(attrs={
                'class': 'form-control price-input',
                'step': '0.01',
                'min': '0'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make price_per_item not required initially since we'll set it automatically
        self.fields['price_per_item'].required = False

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        quantity = cleaned_data.get('quantity')
        price_per_item = cleaned_data.get('price_per_item')
        
        # Auto-set price if item is selected but price is not provided
        if item and not price_per_item:
            cleaned_data['price_per_item'] = item.price
        
        # Validate that we have all required fields
        if not item:
            raise forms.ValidationError("Item is required")
        
        if not quantity or quantity <= 0:
            raise forms.ValidationError("Valid quantity is required")
        
        if not cleaned_data.get('price_per_item') or cleaned_data.get('price_per_item') < 0:
            raise forms.ValidationError("Valid price is required")
        
        return cleaned_data


# Formset for multiple items
InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True
)

"""class InvoiceForm(forms.ModelForm):
    # Add these fields to handle the autocomplete inputs
    customer_search = forms.CharField(required=False, widget=forms.HiddenInput())
    item_search = forms.CharField(required=False, widget=forms.HiddenInput())
    customer_id = forms.CharField(required=False, widget=forms.HiddenInput())
    item_id = forms.CharField(required=False, widget=forms.HiddenInput())

    
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

        def clean(self):
            cleaned_data = super().clean()

            #get ids from hidden fields
            customer_id = cleaned_data.get('customer_id')
            item_id = cleaned_data.get('item_id')

            # convert to actual objects
            if customer_id:
                try:
                    cleaned_data['customer_name'] = Customer.objects.get(id=customer_id)
                except Customer.DoesNotExist:
                    self.add_error['customer_id','selected customer dies not exist']
            if item_id:
                try:
                    item = Item.objects.get(id=int(item_id))
                    cleaned_data['item'] = item

                    if not cleaned_data.get('price_per_item'):
                        cleaned_data['price_per_item' ] = Item.price
                except (Item.DoesNotExist, ValueError, TypeError):
                    raise forms.ValidationError('selected item is invalid')
            return cleaned_data

            def save(self,commit= True):
                instance = super().save(commit=False)

                #set foreignkey from cleaned data

                if 'customer_name' in self.cleaned_data:
                    instance.customer_name - self.cleaned_data['customer']

                if 'item' in self.cleaned_data:
                    instance.item = self.cleaned_data['item']
                
                if commit:
                    instance.save()
                return instance"""