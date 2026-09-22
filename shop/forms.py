from django import forms
from pages.models import Product, Category, Brand
from taggit.forms import TagField
from django_select2.forms import Select2TagWidget


class ProductForm(forms.ModelForm):
    brand_name = forms.CharField(
        label="Brand Name",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter brand name'}),
        required=True
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.all().order_by('name'),
        empty_label="--- Select a Category ---",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Product Category"
    )

    tags = TagField(
        required=False,
        widget=Select2TagWidget(attrs={
            'data-tags': 'true',
            'class': 'form-control',
            'placeholder': 'Enter tags like #trendy, #clothes'
        }),
        help_text='Start typing and select existing tags or create new ones, separated by commas.'
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
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, Select2TagWidget)):
                current_class = field.widget.attrs.get('class', '')
                if 'form-control' not in current_class:
                    field.widget.attrs['class'] = (current_class + ' form-control').strip()
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'

        if self.instance and self.instance.brand:
            self.initial['brand_name'] = self.instance.brand.name

    def save(self, commit=True):
        product = super().save(commit=False)
        brand_name = self.cleaned_data.get('brand_name')
        if brand_name:
            brand, _ = Brand.objects.get_or_create(name=brand_name.strip())
            product.brand = brand
        else:
            product.brand = None

        if commit:
            product.save()
            self.save_m2m()
        return product
