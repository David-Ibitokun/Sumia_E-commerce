"""Forms for the shop app."""
from django import forms
from django_select2.forms import Select2TagWidget
from taggit.forms import TagField

from pages.models import Brand, Category, Order, Product

CHECKOUT_WIDGET_CLASSES = {
    'address': 'form-control rounded-pill',
    'city': 'form-control rounded-pill',
    'zip_code': 'form-control rounded-pill',
    'country': 'form-control rounded-pill',
    'phone_number': 'form-control rounded-pill',
}

#: Payment methods the storefront does not integrate yet.
UNAVAILABLE_PAYMENT_METHODS = {'Card', 'Bank Transfer'}


def payment_method_choices():
    """Storefront payment options, marking the unavailable ones."""
    return [
        (
            value,
            f"{label} (coming soon)" if value in UNAVAILABLE_PAYMENT_METHODS else label,
        )
        for value, label in Order.PAYMENT_METHOD_CHOICES
    ]


class PaymentMethodRadioSelect(forms.RadioSelect):
    """Radio group that renders the not-yet-integrated methods as disabled."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if value in UNAVAILABLE_PAYMENT_METHODS:
            option['attrs']['disabled'] = True
        return option


class TagListWidget(Select2TagWidget):
    """Select2 tag input whose posted values taggit can actually parse.

    Select2 posts a list of values while `taggit.forms.TagField` expects a
    single comma separated string, so the values are joined before validation.
    """

    def value_from_datadict(self, data, files, name):
        values = super().value_from_datadict(data, files, name) or []
        return ','.join(values)


class CheckoutForm(forms.Form):
    """Shipping details and payment method for a new order."""

    address = forms.CharField(
        max_length=255,
        label="Address",
        widget=forms.TextInput(attrs={'placeholder': 'Street address'}),
    )
    city = forms.CharField(
        max_length=100,
        label="City",
        widget=forms.TextInput(attrs={'placeholder': 'City'}),
    )
    zip_code = forms.CharField(
        max_length=20,
        required=False,
        label="Zip Code",
        widget=forms.TextInput(attrs={'placeholder': 'Postal code'}),
    )
    country = forms.CharField(
        max_length=100,
        label="Country",
        widget=forms.TextInput(attrs={'placeholder': 'Country'}),
    )
    phone_number = forms.CharField(
        max_length=20,
        label="Phone Number",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., +1234567890'}),
    )
    payment_method = forms.ChoiceField(
        choices=payment_method_choices(),
        initial=Order.PAYMENT_METHOD_COD,
        label="Payment Method",
        widget=PaymentMethodRadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, css_class in CHECKOUT_WIDGET_CLASSES.items():
            self.fields[name].widget.attrs['class'] = css_class

    def clean_payment_method(self):
        method = self.cleaned_data['payment_method']
        if method in UNAVAILABLE_PAYMENT_METHODS:
            raise forms.ValidationError(
                f"{method} payments are not available yet. "
                "Please choose cash on delivery."
            )
        return method

    def shipping_data(self):
        """Field values ready to pass to ``Order.objects.create``."""
        return {
            'address': self.cleaned_data['address'],
            'city': self.cleaned_data['city'],
            'zip_code': self.cleaned_data['zip_code'],
            'country': self.cleaned_data['country'],
            'phone_number': self.cleaned_data['phone_number'],
            'payment_method': self.cleaned_data['payment_method'],
        }

    @staticmethod
    def shipping_defaults(user):
        """Prefill the form from the signed in user's profile."""
        return {
            'address': getattr(user, 'address', ''),
            'city': getattr(user, 'city', ''),
            'zip_code': getattr(user, 'zip_code', ''),
            'country': getattr(user, 'country', ''),
            'phone_number': getattr(user, 'phone_number', ''),
            'payment_method': Order.PAYMENT_METHOD_COD,
        }


class ProductForm(forms.ModelForm):
    """Create/update form for a vendor's product."""

    brand_name = forms.CharField(
        label="Brand Name",
        max_length=100,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter brand name'}
        ),
        required=True,
    )

    category = forms.ModelChoiceField(
        # Built in __init__ so the queryset is never evaluated at import time.
        queryset=Category.objects.none(),
        empty_label="--- Select a Category ---",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Product Category",
    )

    tags = TagField(
        required=False,
        widget=TagListWidget(attrs={
            'data-tags': 'true',
            'class': 'form-control',
            'placeholder': 'Enter tags like #trendy, #clothes',
        }),
        help_text='Start typing and select existing tags or create new ones, separated by commas.',
    )

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'discount_price',
            'image', 'stock_quantity', 'is_available', 'category', 'tags',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Provide a detailed description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 99.99'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional: e.g., 79.99'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(
            is_active=True
        ).order_by('name')

        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, Select2TagWidget)):
                current_class = field.widget.attrs.get('class', '')
                if 'form-control' not in current_class:
                    field.widget.attrs['class'] = (current_class + ' form-control').strip()
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'

        if self.instance and self.instance.brand_id:
            self.initial['brand_name'] = self.instance.brand.name

    def save(self, commit=True):
        product = super().save(commit=False)
        brand_name = (self.cleaned_data.get('brand_name') or '').strip()
        product.brand = (
            Brand.objects.get_or_create(name=brand_name)[0] if brand_name else None
        )

        if commit:
            product.save()
            self.save_m2m()
        return product
