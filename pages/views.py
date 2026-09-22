from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Category, Product


def home(request):
    products = Product.objects.filter(is_available=True).order_by('-created_at')[:12]
    return render(request, 'index.html', {'products': products})


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


def page404(request):
    return render(request, 'page404.html', status=404)


def page500(request):
    return render(request, 'page500.html', status=500)


def page503(request):
    return render(request, 'page503.html', status=503)


def login(request):
    return render(request, 'login.html')


def register(request):
    return render(request, 'register.html')


def myAccount(request):
    return render(request, 'myAccount.html')


@login_required(login_url='login')
def password_change_done(request):
    return render(request, 'password_change_done.html')
