from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import UsersRegistrationForm, CustomAuthenticationForm
from pages.decorators import customer_required, vendor_required
from shop.services import dashboard as dashboard_service


def register_user(request):
    form = UsersRegistrationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Registration successful. You can now log in.")
        return redirect('login')

    if request.method == 'POST':
        messages.error(request, "Registration failed. Please correct the errors below.")

    return render(request, 'accounts/register.html', {'form': form})


def dashboard_url_for(user):
    """Route a user to the dashboard matching their account type."""
    return 'vendor_dashboard' if user.account_type == 'vendor' else 'user_dashboard'


def login_user(request):
    if request.user.is_authenticated:
        return redirect(dashboard_url_for(request.user))

    form = CustomAuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(dashboard_url_for(user))
        messages.error(request, "Invalid username or password.")

    return render(request, 'accounts/login.html', {'form': form})


def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


@customer_required
def user_dashboard(request):
    """Landing page for a shopper account."""
    return render(
        request,
        'accounts/user_dashboard.html',
        dashboard_service.customer_stats(request.user),
    )


@vendor_required
def vendor_dashboard(request):
    """Landing page for a vendor account: headline figures plus recent activity."""
    return render(
        request,
        'vendor/dashboard.html',
        dashboard_service.vendor_stats(request.user),
    )


@login_required(login_url='login')
def my_profile(request):
    """View and update the signed in user's profile."""
    form = UsersRegistrationForm(
        request.POST or None, instance=request.user
    )

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('my_profile')
        messages.error(request, 'Please correct the error below.')

    return render(request, 'accounts/my_profile.html', {'form': form})
