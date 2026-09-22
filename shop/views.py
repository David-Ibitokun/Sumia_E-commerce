from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import Http404
from django.utils.text import slugify

from pages.models import Product, Category, Brand, Cart, CartItem, Wishlist, Order, OrderItem
from .forms import ProductForm


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    category_ids = [category.id]

    def get_descendant_ids(current_category):
        ids = []
        for subcat in current_category.subcategories.all():
            ids.append(subcat.id)
            ids.extend(get_descendant_ids(subcat))
        return ids

    category_ids.extend(get_descendant_ids(category))
    products = Product.objects.filter(category__id__in=category_ids, is_available=True).order_by('name')

    breadcrumb = []
    current = category
    while current:
        breadcrumb.insert(0, current)
        current = current.parent

    return render(request, 'category_detail.html', {
        'category': category,
        'products': products,
        'breadcrumb': breadcrumb,
    })


def shop(request):
    products = Product.objects.filter(is_available=True).order_by('name')
    return render(request, 'shop.html', {'products': products})


def singleProduct(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    breadcrumb = []
    current_category = product.category
    while current_category:
        breadcrumb.insert(0, current_category)
        current_category = current_category.parent

    related_products = Product.objects.filter(
        category=product.category, is_available=True
    ).exclude(pk=product.pk).order_by('?')[:4]

    return render(request, 'singleProduct.html', {
        'product': product,
        'breadcrumb': breadcrumb,
        'products': related_products,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    category = product.category

    breadcrumb = []
    current = category
    while current:
        breadcrumb.insert(0, current)
        current = current.parent

    related_products = Product.objects.filter(
        category=category, is_available=True
    ).exclude(pk=product.pk).order_by('?')[:4]

    return render(request, 'product_detail.html', {
        'product': product,
        'breadcrumb': breadcrumb,
        'products': related_products,
    })


def view_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = CartItem.objects.filter(cart=cart).order_by('product__name')
        total_price = cart.get_total_price()
    else:
        items = []
        total_price = 0

    return render(request, 'cart.html', {
        'cart_items': items,
        'total_price': total_price,
    })


@login_required(login_url='login')
def add_product(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    selected_category_id = None

    if request.method == 'POST' and 'category' in request.POST:
        try:
            selected_category_id = int(request.POST.get('category'))
        except (TypeError, ValueError):
            selected_category_id = None

    if request.method == 'POST':
        if form.is_valid():
            product = form.save(commit=False)
            if request.user.is_authenticated:
                product.creator = request.user
            else:
                messages.error(request, "Authentication required to add a product.")
                return redirect('login')

            category_id = request.POST.get('category')
            if category_id:
                try:
                    product.category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    messages.error(request, "Selected category does not exist.")
                    product.category = None
            else:
                product.category = None

            try:
                form.save()
                messages.success(request, f"Product '{product.name}' added successfully!")
                return redirect('product_list')
            except IntegrityError as e:
                messages.error(request, f"Database error: {e}")
            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {e}")
        else:
            messages.error(request, "Please correct the errors in the form.")

    context = {
        'form': form,
        'selected_category_id': selected_category_id,
    }
    return render(request, 'add_product.html', context)


@login_required(login_url='login')
def edit_product(request, slug):
    product = get_object_or_404(Product, slug=slug, creator=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            category_id = request.POST.get('category')
            if category_id:
                try:
                    product.category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    messages.error(request, "Selected category does not exist.")
                    product.category = None
            else:
                product.category = None

            try:
                form.save()
                messages.success(request, "Product updated successfully!")
                return redirect('product_list')
            except IntegrityError as e:
                messages.error(request, f"Database error: {e}")
            else:
                messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm(instance=product)

    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'edit_product.html', context)


@login_required(login_url='login')
def delete_product(request, slug):
    product = get_object_or_404(Product, slug=slug, creator=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect('product_list')
    return render(request, 'delete_product_confirm.html', {'product': product})


def brand_list(request):
    brands = Brand.objects.all().order_by('name')
    return render(request, 'brand_list.html', {'brands': brands})


def brand_detail(request, slug=None, pk=None):
    if slug:
        brand = get_object_or_404(Brand, slug=slug)
    elif pk:
        brand = get_object_or_404(Brand, pk=pk)
    else:
        raise Http404("No brand identifier provided.")

    products = Product.objects.filter(brand=brand, is_available=True).order_by('-created_at')
    return render(request, 'brand_detail.html', {
        'brand': brand,
        'products': products,
    })


@login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not product.is_available or product.stock_quantity == 0:
        messages.error(request, f"{product.name} is currently out of stock or unavailable.")
        return redirect(request.META.get('HTTP_REFERER', 'shop'))

    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            raise ValueError
    except (TypeError, ValueError):
        messages.error(request, "Invalid quantity selected.")
        return redirect(request.META.get('HTTP_REFERER', 'shop'))

    if quantity > product.stock_quantity:
        messages.error(request, f"Only {product.stock_quantity} units of {product.name} available.")
        return redirect(request.META.get('HTTP_REFERER', 'shop'))

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        total_quantity = cart_item.quantity + quantity
        if total_quantity > product.stock_quantity:
            available_to_add = product.stock_quantity - cart_item.quantity
            messages.warning(request, f"You can only add {available_to_add} more of {product.name}.")
            return redirect(request.META.get('HTTP_REFERER', 'shop'))
        cart_item.quantity = total_quantity
        cart_item.save()
        messages.success(request, f"Updated {product.name} quantity to {cart_item.quantity}.")
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f"{product.name} added to your cart.")

    return redirect(request.META.get('HTTP_REFERER', 'shop'))


@login_required(login_url='login')
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.info(request, f"{product_name} removed from your cart.")
    return redirect('cart')


@login_required(login_url='login')
def update_cart_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        try:
            new_quantity = int(request.POST.get('quantity', 1))
            if new_quantity <= 0:
                messages.error(request, "Quantity must be at least 1.")
                return redirect('cart')
            if new_quantity > cart_item.product.stock_quantity:
                messages.error(request, f"Cannot update quantity for {cart_item.product.name}. Only {cart_item.product.stock_quantity} available.")
                return redirect('cart')
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, f"Quantity for {cart_item.product.name} updated.")
        except ValueError:
            messages.error(request, "Invalid quantity.")
    return redirect('cart')


@login_required(login_url='login')
def checkout(request):
    user = request.user
    cart, _ = Cart.objects.get_or_create(user=user)
    cart_items = CartItem.objects.filter(cart=cart)

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('shop')

    total_price = cart.get_total_price()

    if request.method == 'POST':
        address = request.POST.get('address')
        city = request.POST.get('city')
        zip_code = request.POST.get('zip_code')
        country = request.POST.get('country')
        phone_number = request.POST.get('phone_number')
        payment_method = request.POST.get('payment_method')

        if not all([address, city, country, payment_method]):
            messages.error(request, "Please fill in all required shipping details and select a payment method.")
            return render(request, 'checkout.html', {
                'cart': cart,
                'cart_items': cart_items,
                'total_price': total_price,
                'address': address, 'city': city, 'zip_code': zip_code, 'country': country,
                'phone_number': phone_number, 'payment_method': payment_method,
            })

        try:
            for item in cart_items:
                product = Product.objects.get(id=item.product.id)
                if item.quantity > product.stock_quantity:
                    messages.error(request, f"Not enough stock for {product.name}.")
                    return redirect('cart')

            order = Order.objects.create(
                user=user, total_price=total_price, is_paid=True,
                address=address, city=city, zip_code=zip_code,
                phone_number=phone_number, country=country, payment_method=payment_method,
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order, product=item.product,
                    quantity=item.quantity, price_at_purchase=item.product.get_display_price(),
                )
                item.product.stock_quantity -= item.quantity
                item.product.save()

            cart_items.delete()
            cart.delete()

            messages.success(request, "Your order has been placed successfully!")
            return render(request, 'checkout.html', {'order': order})
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return render(request, 'checkout.html', {
                'cart': cart, 'cart_items': cart_items, 'total_price': total_price,
                'address': address, 'city': city, 'zip_code': zip_code, 'country': country,
                'phone_number': phone_number, 'payment_method': payment_method,
            })
    else:
        return render(request, 'checkout.html', {
            'cart': cart, 'cart_items': cart_items, 'total_price': total_price,
            'address': user.address if hasattr(user, 'address') else '',
            'city': user.city if hasattr(user, 'city') else '',
            'zip_code': user.zip_code if hasattr(user, 'zip_code') else '',
            'country': user.country if hasattr(user, 'country') else '',
            'phone_number': user.phone_number if hasattr(user, 'phone_number') else '',
            'payment_method': 'COD',
        })


def search(request):
    query = request.GET.get('q')
    products = Product.objects.none()
    category_id = request.GET.get('category', '')

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query) |
            Q(category__name__icontains=query) | Q(tags__name__icontains=query) |
            Q(brand__name__icontains=query)
        ).distinct()

    if category_id:
        try:
            selected_category = Category.objects.get(id=category_id)
            category_ids_to_filter = [selected_category.id]

            def get_descendant_ids(current_category):
                ids = []
                for subcat in current_category.subcategories.all():
                    ids.append(subcat.id)
                    ids.extend(get_descendant_ids(subcat))
                return ids
            category_ids_to_filter.extend(get_descendant_ids(selected_category))
            products = products.filter(category__id__in=category_ids_to_filter)
        except Category.DoesNotExist:
            pass

    return render(request, 'search_results.html', {
        'query': query, 'products': products, 'selected_category_id': category_id,
    })


@login_required(login_url='login')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if created:
            messages.success(request, f"{product.name} added to your wishlist!")
        else:
            messages.info(request, f"{product.name} is already in your wishlist.")
    except Exception as e:
        messages.error(request, f"Could not add {product.name} to wishlist: {e}")
    return redirect(request.META.get('HTTP_REFERER', 'wishlist'))


@login_required(login_url='login')
def remove_from_wishlist(request, item_id):
    try:
        wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
        product_name = wishlist_item.product.name
        wishlist_item.delete()
        messages.info(request, f"{product_name} removed from your wishlist.")
    except Exception as e:
        messages.error(request, f"Error removing item from wishlist: {e}")
    return redirect('wishlist')


@login_required(login_url='login')
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).order_by('-added_at')
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})


@login_required(login_url='login')
def product_list(request):
    products = Product.objects.filter(creator=request.user).order_by('-created_at')
    return render(request, 'product_list.html', {'products': products})


@login_required(login_url='login')
def vendor_orders(request):
    vendor_orders_list = Order.objects.filter(
        orderitem__product__creator=request.user
    ).distinct().select_related('user').annotate(
        vendor_total_amount=Sum(
            F('orderitem__quantity') * F('orderitem__price_at_purchase'),
            filter=Q(orderitem__product__creator=request.user)
        )
    ).order_by('-created_at')

    return render(request, 'vendor_orders.html', {'orders': vendor_orders_list})


@login_required(login_url='login')
def vendor_order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    vendor_order_items = OrderItem.objects.filter(
        order=order, product__creator=request.user
    ).select_related('product')
    vendor_total_price = sum(item.get_total_price() for item in vendor_order_items)

    return render(request, 'order_detail.html', {
        'order': order,
        'vendor_order_items': vendor_order_items,
        'vendor_total_price': vendor_total_price,
    })


@login_required(login_url='login')
def recent_order(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'recent_orders.html', {'orders': orders})


@login_required(login_url='login')
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    order_items = OrderItem.objects.filter(order=order).select_related('product')
    return render(request, 'users_order_detail.html', {
        'order': order,
        'order_items': order_items,
    })


def generate_unique_slug(name):
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
