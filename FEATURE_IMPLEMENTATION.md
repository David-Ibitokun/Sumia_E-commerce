# Feature Implementation Outlines

## 1. Product Review and Rating System

### Models (shop/models/reviews.py)

```python
from django.db import models
from django.conf import settings
from pages.models import Product


class ProductReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'is_approved']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.rating}/5 by {self.user}"
```

### Service Layer (shop/services/reviews.py)

```python
from django.db import models
from django.db.models import Avg, Count
from shop.models.reviews import ProductReview
from shop.services.exceptions import ShopServiceError


class ReviewServiceError(ShopServiceError):
    pass


def create_review(user, product, rating, title, comment):
    """Create a new product review."""
    if hasattr(user, 'reviews') and user.reviews.filter(product=product).exists():
        raise ReviewServiceError("You have already reviewed this product.")

    # Check if user purchased this product
    is_verified = user.orders.filter(
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
    return stats
```

### Views (shop/views/reviews.py)

```python
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from pages.models import Product
from shop.services import reviews as review_service
from shop.forms import ReviewForm


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                review_service.create_review(
                    user=request.user,
                    product=product,
                    rating=form.cleaned_data['rating'],
                    title=form.cleaned_data['title'],
                    comment=form.cleaned_data['comment'],
                )
                messages.success(request, "Thank you for your review!")
            except ReviewServiceError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors below.")
    return redirect('product_detail', slug=product.slug)
```

### Template Tags (shop/templatetags/review_tags.py)

```python
from django import template
from shop.services.reviews import get_product_rating_stats

register = template.Library()


@register.inclusion_tag('shop/includes/rating_display.html')
def show_rating(product):
    stats = get_product_rating_stats(product)
    return {'stats': stats, 'product': product}
```

---

## 2. Product Image Gallery

### Models (shop/models/gallery.py)

```python
from django.db import models
from pages.models import Product


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='gallery_images'
    )
    image = models.ImageField(upload_to='products/gallery/%Y/%m/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
            models.Index(fields=['product', 'sort_order']),
        ]

    def __str__(self):
        return f"{self.product.name} - Image {self.sort_order}"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, is_primary=True
            ).update(is_primary=False)
        super().save(*args, **kwargs)
```

### Service Layer (shop/services/gallery.py)

```python
from django.db import transaction
from shop.models.gallery import ProductImage


def add_product_images(product, images, alt_texts=None):
    """Add multiple images to a product."""
    if alt_texts is None:
        alt_texts = [''] * len(images)

    with transaction.atomic():
        current_count = product.gallery_images.count()
        created = []
        for i, (image, alt_text) in enumerate(zip(images, alt_texts)):
            img = ProductImage.objects.create(
                product=product,
                image=image,
                alt_text=alt_text,
                sort_order=current_count + i,
                is_primary=(current_count == 0 and i == 0),  # First image is primary
            )
            created.append(img)
    return created


def reorder_images(product, image_ids):
    """Reorder gallery images by providing ordered list of IDs."""
    with transaction.atomic():
        for index, image_id in enumerate(image_ids):
            ProductImage.objects.filter(
                id=image_id, product=product
            ).update(sort_order=index)


def set_primary_image(product, image_id):
    """Set a gallery image as primary."""
    ProductImage.objects.filter(product=product).update(is_primary=False)
    ProductImage.objects.filter(id=image_id, product=product).update(
        is_primary=True
    )
```

### Views (shop/views/gallery.py)

```python
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from pages.models import Product
from shop.services import gallery as gallery_service
from shop.forms import ProductImageForm, ProductImageFormSet


@login_required
@user_passes_test(lambda u: u.is_vendor)
def manage_gallery(request, product_id):
    product = get_object_or_404(Product, id=product_id, creator=request.user)

    if request.method == 'POST':
        formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Gallery updated successfully.")
            return redirect('manage_gallery', product_id=product.id)
    else:
        formset = ProductImageFormSet(instance=product)

    return render(request, 'vendor/gallery_manage.html', {
        'product': product,
        'formset': formset,
    })
```

---

## 3. User Notification System

### Models (notifications/models.py)

```python
from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('order_placed', 'Order Placed'),
        ('order_confirmed', 'Order Confirmed'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('order_cancelled', 'Order Cancelled'),
        ('payment_received', 'Payment Received'),
        ('payment_failed', 'Payment Failed'),
        ('review_received', 'Review Received'),
        ('price_drop', 'Price Drop Alert'),
        ('back_in_stock', 'Back in Stock'),
        ('promotional', 'Promotional'),
        ('system', 'System Announcement'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')

    # Optional related object references
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['recipient', 'notification_type']),
        ]

    def __str__(self):
        return f"{self.recipient} - {self.notification_type}: {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
```

### Service Layer (notifications/services.py)

```python
from django.db import transaction
from django.utils import timezone
from notifications.models import Notification


def create_notification(recipient, notification_type, title, message, priority='normal', related_object=None):
    """Create a single notification."""
    data = {
        'recipient': recipient,
        'notification_type': notification_type,
        'title': title,
        'message': message,
        'priority': priority,
    }
    if related_object:
        from django.contrib.contenttypes.models import ContentType
        data['content_type'] = ContentType.objects.get_for_model(related_object)
        data['object_id'] = related_object.pk

    return Notification.objects.create(**data)


def create_bulk_notifications(recipients, notification_type, title, message, priority='normal'):
    """Create notifications for multiple recipients efficiently."""
    notifications = [
        Notification(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
        )
        for recipient in recipients
    ]
    return Notification.objects.bulk_create(notifications)


def get_unread_count(user):
    """Get count of unread notifications for a user."""
    return user.notifications.filter(is_read=False).count()


def mark_all_as_read(user):
    """Mark all user's notifications as read."""
    user.notifications.filter(is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )


def get_user_notifications(user, unread_only=False, limit=None):
    """Get notifications for a user with optional filters."""
    queryset = user.notifications.all()
    if unread_only:
        queryset = queryset.filter(is_read=False)
    if limit:
        queryset = queryset[:limit]
    return queryset
```

### Views (notifications/views.py)

```python
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from notifications.services import (
    get_user_notifications,
    get_unread_count,
    mark_all_as_read,
)


@login_required
def notification_list(request):
    """Display user's notifications."""
    notifications = get_user_notifications(request.user)
    unread_count = get_unread_count(request.user)
    return render(request, 'notifications/list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a single notification as read via AJAX."""
    notification = request.user.notifications.filter(id=notification_id).first()
    if notification:
        notification.mark_as_read()
        return JsonResponse({'success': True, 'unread_count': get_unread_count(request.user)})
    return JsonResponse({'success': False}, status=404)


@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read via AJAX."""
    mark_all_as_read(request.user)
    return JsonResponse({'success': True, 'unread_count': 0})


@login_required
def notification_badge(request):
    """Return unread count for navbar badge (AJAX)."""
    return JsonResponse({'unread_count': get_unread_count(request.user)})
```

### Template Inclusion (templates/includes/notification_badge.html)

```html
{% if user.is_authenticated %}
  <div class="notification-badge" id="notification-badge" data-url="{% url 'notification_badge' %}">
    <a href="{% url 'notification_list' %}">
      <i class="bi bi-bell"></i>
      <span class="badge bg-danger" id="unread-count">{{ unread_count|default:0 }}</span>
    </a>
  </div>
{% endif %}
```

### JavaScript (static/js/notifications.js)

```javascript
// Auto-refresh notification badge every 30 seconds
function updateNotificationBadge() {
    const badge = document.getElementById('notification-badge');
    if (!badge) return;

    fetch(badge.dataset.url)
        .then(response => response.json())
        .then(data => {
            const countEl = document.getElementById('unread-count');
            if (countEl) {
                countEl.textContent = data.unread_count;
                countEl.style.display = data.unread_count > 0 ? 'inline' : 'none';
            }
        })
        .catch(console.error);
}

setInterval(updateNotificationBadge, 30000);
updateNotificationBadge(); // Initial load
```

---

## Implementation Order

1. **Product Review System** - Add models, run migrations, create forms/views, integrate with product detail
2. **Product Image Gallery** - Add models, run migrations, create vendor management UI
3. **Notification System** - Create separate `notifications` app, add models, create services, build frontend integration

## Migration Commands

```bash
# After adding each feature's models:
python manage.py makemigrations
python manage.py migrate
```

## Required Template Updates

- `product_detail.html` - Add review display and submission form
- `vendor/product_form.html` - Add image gallery management
- `base.html` - Add notification badge to navbar
- Create new templates for notification list and review forms