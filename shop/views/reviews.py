"""Product review submission and management."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from pages.models import Product
from shop.services import reviews as review_service
from shop.forms import ReviewForm


@login_required(login_url='login')
def add_review(request, product_id):
    """Submit a review for a product."""
    product = get_object_or_404(Product, id=product_id, is_available=True)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                review_service.create_review(
                    user=request.user,
                    product=product,
                    rating=int(form.cleaned_data['rating']),
                    title=form.cleaned_data['title'],
                    comment=form.cleaned_data['comment'],
                )
                messages.success(request, "Thank you! Your review has been submitted.")
            except review_service.ReviewServiceError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors in your review submission.")
    return redirect('product_detail', slug=product.slug)
