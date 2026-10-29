"""DRF API Views for Sumia Catalog."""
from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter
from pages.models import Product, Category, Brand
from .serializers import ProductSerializer, CategorySerializer, BrandSerializer


@extend_schema(tags=['Products'], summary='List available products with optional category filtering')
class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Product.objects.filter(is_available=True).select_related('category', 'brand')
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset


@extend_schema(tags=['Products'], summary='Retrieve detailed product by slug')
class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_available=True).select_related('category', 'brand')
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=['Categories'], summary='List top-level product categories')
class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=['Brands'], summary='List active brands')
class BrandListAPIView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.AllowAny]
