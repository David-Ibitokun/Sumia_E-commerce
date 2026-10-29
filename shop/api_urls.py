"""API Route declarations for shop catalog endpoints."""
from django.urls import path
from .api_views import (
    ProductListAPIView,
    ProductDetailAPIView,
    CategoryListAPIView,
    BrandListAPIView,
)

urlpatterns = [
    path('products/', ProductListAPIView.as_view(), name='api_product_list'),
    path('products/<slug:slug>/', ProductDetailAPIView.as_view(), name='api_product_detail'),
    path('categories/', CategoryListAPIView.as_view(), name='api_category_list'),
    path('brands/', BrandListAPIView.as_view(), name='api_brand_list'),
]
