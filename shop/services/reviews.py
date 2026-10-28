"""Service layer for product reviews and ratings."""
from django.db import models
from django.db.models import Avg, Count
from pages.models import ProductReview
from shop.services.exceptions import ShopServiceError


class ReviewServiceError(ShopServiceError):
    pass


def create_review(user, product, rating, title, comment):
    """Create a new product review."""
    if ProductReview.objects.filter(product=product, user=user).exists():
        raise ReviewServiceError("You have already reviewed this product.")

    # Check if user purchased this product
    is_verified = False
    if hasattr(user, 'order_set'):
        is_verified = user.order_set.filter(
            orderitem__product=product,
            is_paid=True
        ).exists()

    review = ProductReview.objects.create(
        user=user,
        product=product,
        rating=rating,
        title=title,
        comment=comment,
        is_verified_purchase=is_verified,
    )
    return review


def get_product_reviews(product, approved_only=True):
    """Get reviews for a product with optional approval filter."""
    queryset = product.reviews.select_related('user')
    if approved_only:
        queryset = queryset.filter(is_approved=True)
    return queryset


def get_product_rating_stats(product):
    """Get aggregated rating statistics for a product."""
    reviews = product.reviews.filter(is_approved=True)
    stats = reviews.aggregate(
        average_rating=Avg('rating'),
        total_reviews=Count('id'),
        rating_1=Count('id', filter=models.Q(rating=1)),
        rating_2=Count('id', filter=models.Q(rating=2)),
        rating_3=Count('id', filter=models.Q(rating=3)),
        rating_4=Count('id', filter=models.Q(rating=4)),
        rating_5=Count('id', filter=models.Q(rating=5)),
    )
    if stats['average_rating'] is not None:
        stats['average_rating'] = round(stats['average_rating'], 1)
    else:
        stats['average_rating'] = 0.0
    return stats
