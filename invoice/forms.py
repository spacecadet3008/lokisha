from django import forms
from .models import Invoice,InvoiceItem,Delivery,DeliveryItem
from store.models import Item
from accounts.models import Customer
from django.forms import inlineformset_factory


class InvoiceForm(forms.ModelForm):
    customer_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control customer-search',
            'placeholder': 'Search for customer...',
            'autocomplete': 'off'
        }),
        label='Search Customer'
    )
    
    class Meta:
        model = Invoice
        fields = ['customer_name', 'contact_number', 'shipping', 'is_proforma', 'status']
        widgets = {
            'customer_name': forms.HiddenInput(),  # Hidden field for the actual selection
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact number...'
            }),
            'shipping': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'is_proforma': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make customer_name not required initially since we'll set it via search
        self.fields['customer_name'].required = False


class InvoiceItemForm(forms.ModelForm):
    item_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control item-search',
            'placeholder': 'Search for item...',
            'autocomplete': 'off'
        }),
        label='Search Item'
    )
    
    class Meta:
        model = InvoiceItem
        fields = ['item', 'quantity', 'price_per_item']
        widgets = {
            'item': forms.HiddenInput(),  # Hidden field for the actual selection
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
        # Make item not required initially since we'll set it via search
        self.fields['item'].required = False
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

class DeliveryForm(forms.ModelForm):
    customer_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control customer-search',
            'placeholder': 'Search for customer...',
            'autocomplete': 'off'
        }),
        label='Search Customer'
    )
    
    class Meta:
        model = Delivery
        fields = ['customer_name', 'contact_number', 'shipping_address', 'notes', 'status']
        widgets = {
            'customer_name': forms.HiddenInput(),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact number...'
            }),
            'shipping_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter delivery address...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional delivery notes...'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer_name'].required = False
        
        # Pre-populate customer search if instance exists
        if self.instance and self.instance.pk and self.instance.customer_name:
            customer = self.instance.customer_name
            self.fields['customer_search'].initial = f"{customer.first_name} {customer.last_name}"

class DeliveryItemForm(forms.ModelForm):
    item_search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control item-search', 'placeholder': 'Search for item...'
    }))
    
    class Meta:
        model = DeliveryItem
        fields = ['item', 'quantity', 'price_per_item']
        widgets = {
            'item': forms.HiddenInput(),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'price_per_item': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }


# Formset for delivery items
DeliveryItemFormSet = inlineformset_factory(
    Delivery,
    DeliveryItem,
    form=DeliveryItemForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True
)
