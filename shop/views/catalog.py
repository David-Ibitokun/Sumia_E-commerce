"""Product management for vendors: their own product list and CRUD.

`ProductForm` already owns the `category` and `brand` fields, so these views
only deal with ownership, persistence and user feedback.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from pages.models import Product

from shop.forms import ProductForm
from shop.services import categories as category_service


def category_selection(form, product=None):
    """Ids the category accordion needs to reopen the right panel.

    Without this a re-rendered form (after a validation error, or when editing)
    would show no category ticked, because the radios are plain HTML rather
    than `{{ form.category }}`.
    """
    if product is not None:
        category_id = product.category_id
    elif form.is_bound:
        category_id = form.data.get('category')
    else:
        category_id = None

    try:
        category_id = int(category_id) if category_id else None
    except (TypeError, ValueError):
        category_id = None

    return {
        'selected_category_id': category_id,
        'selected_parent_id': category_service.top_level_ancestor_id(category_id),
    }


@login_required(login_url='login')
def product_list(request):
    """Products created by the signed in vendor."""
    products = Product.objects.filter(creator=request.user).order_by('-created_at')
    return render(request, 'vendor/product_list.html', {'products': products})


@login_required(login_url='login')
def add_product(request):
    """Create a product owned by the signed in vendor."""
    form = ProductForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            product = form.save(commit=False)
            product.creator = request.user
            try:
                form.save()
            except IntegrityError:
                messages.error(request, "A product with these details already exists.")
            else:
                messages.success(request, f"Product '{product.name}' added successfully!")
                return redirect('product_list')
        else:
            messages.error(request, "Please correct the errors in the form.")

    return render(
        request,
        'vendor/add_product.html',
        {'form': form, **category_selection(form)},
    )


@login_required(login_url='login')
def edit_product(request, slug):
    """Update one of the signed in vendor's products."""
    product = get_object_or_404(Product, slug=slug, creator=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                messages.error(request, "A product with these details already exists.")
            else:
                messages.success(request, "Product updated successfully!")
                return redirect('product_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        'vendor/edit_product.html',
        {'form': form, 'product': product, **category_selection(form, product)},
    )


@login_required(login_url='login')
def delete_product(request, slug):
    """Confirm and delete one of the signed in vendor's products."""
    product = get_object_or_404(Product, slug=slug, creator=request.user)

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully!")
        return redirect('product_list')

    return render(request, 'vendor/delete_product_confirm.html', {'product': product})
