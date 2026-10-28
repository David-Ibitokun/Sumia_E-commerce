from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Brand, Cart, CartItem, Wishlist, Order, OrderItem, ProductReview, ProductImage

# Inline: Show Products under a Brand
class ProductInlineByBrand(admin.TabularInline):
    model = Product
    extra = 0
    fields = ('name', 'price', 'stock_quantity', 'is_available')
    # Use readonly_fields for fields not directly editable here
    readonly_fields = ('name', 'price', 'stock_quantity', 'is_available')
    can_delete = False
    show_change_link = True # Allows navigating to the product's own change page

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'product_count', 'is_active', 'created_at', 'updated_at') # Added timestamps
    search_fields = ('name',)
    list_filter = ('parent', 'is_active') # Added is_active to filter
    prepopulated_fields = {'slug': ('name',)}

    # Method to count products linked to this category (ForeignKey reverse lookup)
    def product_count(self, obj):
        # obj.products_in_category.count() is the correct reverse lookup for the ForeignKey
        # 'products_in_category' is the related_name we defined on the Product model's 'category' field.
        return obj.products_in_category.count()
    product_count.short_description = 'Number of Products'

    # Removed icon_display because the Category model provided earlier did not have an 'icon' field.
    # If your Category model *does* have an 'icon' field, you'll need to add it back to models.py.
    # def icon_display(self, obj):
    #     if obj.icon:
    #         return format_html(f'<i class="{obj.icon}"></i> {obj.icon}')
    #     return '-'
    # icon_display.short_description = 'Icon'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count', 'created_at', 'updated_at') # Added timestamps
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)} # Add prepopulated slug for brand
    inlines = [ProductInlineByBrand]

    # Method to count products linked to this brand (ForeignKey reverse lookup)
    # obj.products.count() is the correct reverse lookup for the ForeignKey
    # 'products' is the related_name we defined on the Product model's 'brand' field.
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Number of Products'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'display_category', # <--- CHANGED: Now calls the custom method
        'brand',
        'price',
        'discount_price',
        'stock_quantity',
        'is_available',
        'creator', # This is correctly included in list_display
        'created_at',
        'updated_at', # Added updated_at to list_display
    )
    # Added 'category' to list_filter
    list_filter = ('is_available', 'brand', 'category')
    # Added 'brand__name' for searching by brand name, and 'tags__name' for django-taggit
    search_fields = ('name', 'description', 'brand__name', 'tags__name')
    prepopulated_fields = {'slug': ('name',)} # Auto-populate slug
    raw_id_fields = ('brand', 'creator') # This will make creator editable via ID lookup

    # CHANGED: Custom method to display the single category name for a product
    def display_category(self, obj):
        # Safely checks if obj.category exists before trying to access its name
        return obj.category.name if obj.category else 'Uncategorized'
    display_category.short_description = 'Category' # Sets the column header in the admin list


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'get_total_price')
    search_fields = ('user__username',)
    # inlines = [CartItemInline] # You could add an inline here for cart items

    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = 'Total Price'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'get_total_price_item')
    search_fields = ('cart__user__username', 'product__name')
    autocomplete_fields = ['cart', 'product'] # Good for large numbers of carts/products

    def get_total_price_item(self, obj):
        return obj.get_total_price()
    get_total_price_item.short_description = 'Item Total'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('added_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('user__username', 'id')
    raw_id_fields = ('user',) # Use raw_id_fields for user if many users
    inlines = [] # You could add an OrderItemInline here

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_at_purchase', 'get_total')
    search_fields = ('order__id', 'product__name')
    raw_id_fields = ('order', 'product')

    def get_total(self, obj):
        return obj.get_total_price()
    get_total.short_description = 'Total'


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'is_verified_purchase', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'is_verified_purchase', 'created_at')
    search_fields = ('product__name', 'user__username', 'title', 'comment')
    raw_id_fields = ('product', 'user')
    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    reject_reviews.short_description = "Reject selected reviews"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'is_primary', 'sort_order', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('product__name', 'alt_text')
    raw_id_fields = ('product',)
