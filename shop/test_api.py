"""Tests for OpenAPI Schema, Swagger UI, and REST API endpoints."""
from django.test import TestCase
from django.urls import reverse
from pages.models import Category, Brand, Product
from authentications.models import UsersRegistration


class SwaggerAndAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vendor = UsersRegistration.objects.create_user(
            username='api_vendor',
            email='api_vendor@example.com',
            password='Password123!',
            account_type='vendor',
        )
        cls.category = Category.objects.create(name='Computers', slug='computers')
        cls.brand = Brand.objects.create(name='TechCorp', slug='techcorp')
        cls.product = Product.objects.create(
            creator=cls.vendor,
            name='TechBook Pro',
            slug='techbook-pro',
            price=250000,
            stock_quantity=10,
            category=cls.category,
            brand=cls.brand,
            is_available=True,
        )

    def test_openapi_schema_endpoint(self):
        response = self.client.get(reverse('schema'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('openapi', response.content.decode('utf-8'))

    def test_swagger_ui_endpoint(self):
        response = self.client.get(reverse('swagger-ui'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'swagger-ui')
        self.assertContains(response, 'Sumia E-Commerce Platform API')

    def test_redoc_endpoint(self):
        response = self.client.get(reverse('redoc'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'redoc')

    def test_api_products_list(self):
        response = self.client.get(reverse('api_product_list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'TechBook Pro')
        self.assertEqual(data[0]['category_name'], 'Computers')

    def test_api_product_detail(self):
        response = self.client.get(reverse('api_product_detail', kwargs={'slug': 'techbook-pro'}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'TechBook Pro')

    def test_api_categories_list(self):
        response = self.client.get(reverse('api_category_list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)

    def test_api_brands_list(self):
        response = self.client.get(reverse('api_brand_list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)
