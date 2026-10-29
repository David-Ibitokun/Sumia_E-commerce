from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UsersRegistration


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form with improved styling"""
    username = forms.CharField(
        label='Username',
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Enter your username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Enter your password',
        })
    )

class UsersRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label='First Name',
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        label='Last Name',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        label='Email Address',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Enter your email address'
        })
    )
    account_type = forms.ChoiceField(
        label='Account Type',
        choices=UsersRegistration.ACCOUNT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-custom'})
    )
    agreed_to_terms = forms.BooleanField(
        label='I agree to the terms and conditions',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta(UserCreationForm.Meta):
        model = UsersRegistration
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'account_type',
            'agreed_to_terms',
            'password1',
            'password2',
        )

        # Set widgets for all fields with custom styling
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Create a username'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Create a password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Confirm password'
            }),
        }

    def clean_email(self):
        from django.utils.html import strip_tags
        email = strip_tags(self.cleaned_data.get('email', '')).strip().lower()
        if UsersRegistration.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email address already exists.')
        return email

    def clean_first_name(self):
        from django.utils.html import strip_tags
        return strip_tags(self.cleaned_data.get('first_name', '')).strip()

    def clean_last_name(self):
        from django.utils.html import strip_tags
        return strip_tags(self.cleaned_data.get('last_name', '')).strip()


class ProfileForm(forms.ModelForm):
    """Profile editing form.

    Deliberately excludes ``account_type`` and ``agreed_to_terms``: those are
    set at registration (or by an administrator) and must never be editable
    through a self-service profile page, otherwise any signed-in user can
    promote themselves to a vendor.
    """

    first_name = forms.CharField(
        label='First Name',
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        label='Last Name',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        label='Email Address',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Enter your email address'
        })
    )

    class Meta:
        model = UsersRegistration
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Enter your username',
                'readonly': True,
            }),
        }

    def clean_email(self):
        from django.utils.html import strip_tags
        email = strip_tags(self.cleaned_data.get('email', '')).strip().lower()
        if UsersRegistration.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email address is already in use by another account.')
        return email

    def clean_first_name(self):
        from django.utils.html import strip_tags
        return strip_tags(self.cleaned_data.get('first_name', '')).strip()

    def clean_last_name(self):
        from django.utils.html import strip_tags
        return strip_tags(self.cleaned_data.get('last_name', '')).strip()

