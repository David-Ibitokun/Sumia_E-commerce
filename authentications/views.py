from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import UsersRegistrationForm, CustomAuthenticationForm
from pages.models import Product


def register_user(request):
    if request.method == 'POST':
        form = UsersRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful. You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
            print(form.errors)
    else:
        form = UsersRegistrationForm()

    return render(request, 'register.html', {'form': form})


def login_user(request):
    if request.user.is_authenticated:
        if request.user.account_type == 'vendor':
            return redirect('vendor_dashboard')
        else:
            return redirect('user_dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")

                if user.account_type == 'vendor':
                    return redirect('vendor_dashboard')
                else:
                    return redirect('user_dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please enter your username and password.")
    else:
        form = CustomAuthenticationForm()

    return render(request, 'login.html', {'form': form})


def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def user_dashboard(request):
    if request.user.account_type != 'user':
        messages.warning(request, "You do not have permission to view this page.")
        return redirect('vendor_dashboard')
    return render(request, 'user_dashboard.html')


@login_required
def vendor_dashboard(request):
    if request.user.account_type != 'vendor':
        messages.warning(request, "You do not have permission to view this page.")
        return redirect('user_dashboard')

    products = Product.objects.filter(creator=request.user)
    return render(request, 'vendor_dashboard.html', {'products': products})


@login_required(login_url='login')
def myProfile(request):
    if request.method == 'POST':
        form = UsersRegistrationForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('myProfile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = UsersRegistrationForm(instance=request.user)

    return render(request, 'myProfile.html', {'form': form})
