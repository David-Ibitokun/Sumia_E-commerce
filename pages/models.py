from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.urls import reverse
from taggit.managers import TaggableManager # For django-taggit
import uuid # Import uuid for generating unique identifiers
from django.utils import timezone # Import timezone for date-based unique numbers

User = get_user_model() # Get the currently active user model

# --- Core E-commerce Models ---

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Font Awesome 6 icon class (e.g., 'fa-solid fa-laptop'). Auto-assigned if empty."
    )

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    CATEGORY_ICON_MAP = {
        'phones': 'fa-solid fa-mobile-alt', 'tablets': 'fa-solid fa-tablet-alt',
        'electronics': 'fa-solid fa-tv', 'computing': 'fa-solid fa-laptop',
        'laptops': 'fa-solid fa-laptop', 'desktops': 'fa-solid fa-desktop',
        'fashion': 'fa-solid fa-shirt', 'clothing': 'fa-solid fa-shirt',
        'shoes': 'fa-solid fa-shoe-prints', 'beauty': 'fa-solid fa-spa',
        'health': 'fa-solid fa-heart-pulse', 'home': 'fa-solid fa-house',
        'kitchen': 'fa-solid fa-blender', 'baby': 'fa-solid fa-baby',
        'kids': 'fa-solid fa-child', 'toys': 'fa-solid fa-robot',
        'sports': 'fa-solid fa-dumbbell', 'fitness': 'fa-solid fa-running',
        'automotive': 'fa-solid fa-car', 'motorcycles': 'fa-solid fa-motorcycle',
        'books': 'fa-solid fa-book', 'media': 'fa-solid fa-compact-disc',
        'gaming': 'fa-solid fa-gamepad', 'groceries': 'fa-solid fa-basket-shopping',
        'food': 'fa-solid fa-apple-whole', 'office': 'fa-solid fa-briefcase',
        'school': 'fa-solid fa-pencil-alt', 'arts': 'fa-solid fa-palette',
        'crafts': 'fa-solid fa-scissors', 'travel': 'fa-solid fa-suitcase-rolling',
        'luggage': 'fa-solid fa-suitcase', 'pets': 'fa-solid fa-paw',
        'industrial': 'fa-solid fa-industry', 'scientific': 'fa-solid fa-flask',
        'renewable': 'fa-solid fa-solar-panel', 'solar': 'fa-solid fa-sun',
        'power': 'fa-solid fa-bolt', 'smartphones': 'fa-solid fa-mobile-alt',
        'tablets': 'fa-solid fa-tablet-alt', 'televisions': 'fa-solid fa-tv',
        'cameras': 'fa-solid fa-camera', 'printers': 'fa-solid fa-print',
        'fragrances': 'fa-solid fa-spray-can', 'skincare': 'fa-solid fa-face-mask',
        'cookware': 'fa-solid fa-utensils', 'appliances': 'fa-solid fa-fan',
        'diapers': 'fa-solid fa-baby-carriage', 'strollers': 'fa-solid fa-baby-carriage',
        'consoles': 'fa-solid fa-gamepad', 'stationery': 'fa-solid fa-pen-fancy',
        'suitcases': 'fa-solid fa-suitcase-rolling', 'dog food': 'fa-solid fa-dog',
        'cat food': 'fa-solid fa-cat', 'test instruments': 'fa-solid fa-microscope',
        'power tools': 'fa-solid fa-screwdriver-wrench', 'inverters': 'fa-solid fa-charging-station',
        'batteries': 'fa-solid fa-battery-full',
    }
    DEFAULT_ICON = 'fa-solid fa-tag' # Fallback icon

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.name)
            queryset = Category.objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            unique_slug = original_slug
            num = 1
            while queryset.filter(slug=unique_slug).exists():
                unique_slug = f"{original_slug}-{num}"
                num += 1
            self.slug = unique_slug
        
        if not self.icon:
            category_name_lower = self.name.lower()
            assigned_icon = None
            for keyword, icon_class in self.CATEGORY_ICON_MAP.items():
                if keyword in category_name_lower:
                    assigned_icon = icon_class
                    break
            if assigned_icon:
                self.icon = assigned_icon
            else:
                self.icon = self.DEFAULT_ICON
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_ancestors(self):
        ancestors = []
        current = self
        while current.parent:
            ancestors.insert(0, current.parent)
            current = current.parent
        return ancestors

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='brands/logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.name)
            queryset = Brand.objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            unique_slug = original_slug
            num = 1
            while queryset.filter(slug=unique_slug).exists():
                unique_slug = f"{original_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('brand_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='products/images/')
    stock_quantity = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_products')

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products_in_category'
    )

    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    tags = TaggableManager(blank=True) # For django-taggit

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.name)
            queryset = Product.objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            unique_slug = original_slug
            num = 1
            while queryset.filter(slug=unique_slug).exists():
                unique_slug = f"{original_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    def get_discount_percent(self):
        if self.discount_price and self.price:
            discount = ((self.price - self.discount_price) / self.price) * 100
            return round(discount)
        return 0

    def get_display_price(self):
        if self.discount_price:
            return self.discount_price
        return self.price

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.cartitem_set.all())

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        return self.quantity * self.product.get_display_price()

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in {self.cart.user.username}'s cart"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product') # A user can only add a product once to wishlist
        ordering = ['-added_at']
        verbose_name_plural = 'Wishlist Items'

    def __str__(self):
        return f"{self.product.name} in {self.user.username}'s wishlist"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_METHOD_COD = 'COD'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_COD, 'Cash on Delivery'),
        ('Card', 'Credit/Debit Card'),
        ('Bank Transfer', 'Bank Transfer'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    # Shipping Information
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Payment Method
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='COD')

    # NEW FIELD: Unique order number (acts as slug)
    order_number = models.CharField(max_length=50, unique=True, blank=True, null=True)

    # Optional: For guest users or tracking sessions
    session_key = models.CharField(max_length=40, blank=True, null=True,
                                   help_text="Session key for guest orders if user is not logged in.")

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate a unique order number using date and a short UUID part
            today_str = timezone.now().strftime('%Y%m%d')
            unique_part = uuid.uuid4().hex[:8].upper() # Use first 8 chars of UUID
            
            new_order_number = f"{today_str}-{unique_part}"
            
            # Ensure uniqueness in case of extremely rare UUID collision
            while Order.objects.filter(order_number=new_order_number).exists():
                unique_part = uuid.uuid4().hex[:8].upper()
                new_order_number = f"{today_str}-{unique_part}"
            
            self.order_number = new_order_number
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # This will be the URL for the user's order detail page
        return reverse('order_detail', kwargs={'order_number': self.order_number})

    def __str__(self):
        return f"Order {self.order_number} by {self.user.username if self.user else 'Guest'}"

    def get_order_items(self):
        return self.orderitem_set.all()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True) # Product can be null if deleted
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2) # Store price at time of order

    def get_total_price(self):
        return self.quantity * self.price_at_purchase

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'} in Order {self.order.order_number}"
