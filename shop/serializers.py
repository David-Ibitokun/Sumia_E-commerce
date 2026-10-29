"""DRF Serializers for Sumia Storefront & Catalog REST APIs."""
from rest_framework import serializers
from pages.models import Category, Brand, Product, ProductReview


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo']


class ProductReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'username', 'rating', 'title', 'comment', 'is_verified_purchase', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'price',
            'discount_price',
            'stock_quantity',
            'category',
            'category_name',
            'brand',
            'brand_name',
            'image',
            'is_available',
            'created_at',
        ]
