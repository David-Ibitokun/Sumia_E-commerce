from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .forms import ProfileForm, UsersRegistrationForm, CustomAuthenticationForm
from pages.decorators import customer_required, vendor_required
from pages.ratelimit import ratelimit
from shop.services import dashboard as dashboard_service


@ratelimit(capacity=10, refill_rate=0.2, key_prefix='rl_register')
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


@ratelimit(capacity=5, refill_rate=0.1, key_prefix='rl_login')
def login_user(request):
    if request.user.is_authenticated:
        return redirect(dashboard_url_for(request.user))

    form = CustomAuthenticationForm(request, data=request.POST or None)
    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")

            # Validate next URL against allowed hosts to prevent Open Redirect attacks
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure()
            ):
                return redirect(next_url)

            return redirect(dashboard_url_for(user))
        messages.error(request, "Invalid username or password.")

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


@require_http_methods(['GET', 'POST'])
def logout_user(request):
    """Log out the current user. Supports POST (CSRF protected) and GET fallback."""
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
    form = ProfileForm(
        request.POST or None, instance=request.user
    )

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('my_profile')
        messages.error(request, 'Please correct the error below.')

    return render(request, 'accounts/my_profile.html', {'form': form})
