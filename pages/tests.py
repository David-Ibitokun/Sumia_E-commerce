import io
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from authentications.models import UsersRegistration
from pages.models import Brand, Category, Product, ProductImage
from pages.utils.images import convert_image_to_webp


class WebPConversionTests(TestCase):
    def setUp(self):
        self.user = UsersRegistration.objects.create_user(
            username='vendor_webp',
            password='password123',
            email='vendor@test.com',
            account_type='vendor'
        )
        self.category = Category.objects.create(name='Electronics')

    def _create_sample_image(self, format='PNG', size=(200, 200), color=(255, 0, 0)):
        buffer = io.BytesIO()
        img = Image.new('RGB', size, color=color)
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer.getvalue()

    def test_convert_image_to_webp_utility(self):
        png_bytes = self._create_sample_image('PNG')
        uploaded = SimpleUploadedFile('sample_test.png', png_bytes, content_type='image/png')
        converted = convert_image_to_webp(uploaded)
        
        self.assertTrue(converted.name.endswith('.webp'))
        # Verify it is valid WebP data
        img = Image.open(converted)
        self.assertEqual(img.format, 'WEBP')

    def test_product_image_auto_converts_to_webp_on_save(self):
        png_bytes = self._create_sample_image('PNG')
        uploaded = SimpleUploadedFile('laptop_cover.png', png_bytes, content_type='image/png')
        
        product = Product.objects.create(
            creator=self.user,
            name='Test Laptop WebP',
            price=150000,
            stock_quantity=5,
            category=self.category,
            image=uploaded
        )
        
        self.assertTrue(product.image.name.endswith('.webp'))
        # Open saved file to verify format
        img = Image.open(product.image)
        self.assertEqual(img.format, 'WEBP')

    def test_brand_logo_auto_converts_to_webp(self):
        jpeg_bytes = self._create_sample_image('JPEG')
        uploaded = SimpleUploadedFile('brand_badge.jpg', jpeg_bytes, content_type='image/jpeg')
        
        brand = Brand.objects.create(
            name='Sony WebP Brand',
            logo=uploaded
        )
        
        self.assertTrue(brand.logo.name.endswith('.webp'))
        img = Image.open(brand.logo)
        self.assertEqual(img.format, 'WEBP')

    def test_gallery_image_auto_converts_to_webp(self):
        png_bytes = self._create_sample_image('PNG')
        uploaded = SimpleUploadedFile('gallery_pic.png', png_bytes, content_type='image/png')
        
        product = Product.objects.create(
            creator=self.user,
            name='Camera WebP',
            price=95000,
            stock_quantity=3,
            category=self.category,
            image=SimpleUploadedFile('camera.png', png_bytes, content_type='image/png')
        )
        
        gallery = ProductImage.objects.create(
            product=product,
            image=uploaded
        )
        
        self.assertTrue(gallery.image.name.endswith('.webp'))
        img = Image.open(gallery.image)
        self.assertEqual(img.format, 'WEBP')



class HealthCheckAndCacheTests(TestCase):
    def test_health_check_endpoint(self):
        from django.urls import reverse
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['database'], 'connected')
        self.assertIn(data['cache'], ('connected', 'degraded'))

    def test_cache_set_and_get(self):
        from django.core.cache import cache
        cache.set('redis_test_ping', 'pong', timeout=10)
        self.assertEqual(cache.get('redis_test_ping'), 'pong')
