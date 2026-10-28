"""Tests for Product Reviews, Gallery, Database Constraints, and Health Check."""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from pages.models import Cart, CartItem, Product, ProductReview, ProductImage
from shop.services import reviews as review_service
from shop.services import gallery as gallery_service

User = get_user_model()

PNG_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08'
    b'\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00'
    b'\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


class ReviewAndGalleryTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reviewer', password='pass12345', account_type='user'
        )
        self.user2 = User.objects.create_user(
            username='reviewer2', password='pass12345', account_type='user'
        )
        self.product = Product.objects.create(
            name='Test Item',
            description='A test item',
            price=2500,
            stock_quantity=10,
            image=SimpleUploadedFile('test.png', PNG_BYTES, content_type='image/png'),
        )

    def test_create_review_service(self):
        review = review_service.create_review(
            user=self.user,
            product=self.product,
            rating=5,
            title='Great product!',
            comment='Really liked it.',
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.user, self.user)

    def test_duplicate_review_raises_error(self):
        review_service.create_review(
            user=self.user,
            product=self.product,
            rating=4,
            title='Good',
            comment='Nice quality',
        )
        with self.assertRaises(review_service.ReviewServiceError):
            review_service.create_review(
                user=self.user,
                product=self.product,
                rating=5,
                title='Second Review',
                comment='Should fail',
            )

    def test_product_rating_stats(self):
        review_service.create_review(
            user=self.user,
            product=self.product,
            rating=5,
            title='Awesome',
            comment='Best ever',
        )
        review_service.create_review(
            user=self.user2,
            product=self.product,
            rating=3,
            title='Average',
            comment='Okay quality',
        )

        stats = review_service.get_product_rating_stats(self.product)
        self.assertEqual(stats['total_reviews'], 2)
        self.assertEqual(stats['average_rating'], 4.0)
        self.assertEqual(stats['rating_5'], 1)
        self.assertEqual(stats['rating_3'], 1)

    def test_add_review_view(self):
        self.client.login(username='reviewer', password='pass12345')
        response = self.client.post(
            reverse('add_review', args=[self.product.id]),
            {'rating': 5, 'title': 'Superb', 'comment': 'Highly recommended'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ProductReview.objects.filter(product=self.product, user=self.user).exists())

    def test_gallery_service(self):
        img1 = SimpleUploadedFile('gallery1.png', PNG_BYTES, content_type='image/png')
        img2 = SimpleUploadedFile('gallery2.png', PNG_BYTES, content_type='image/png')

        created = gallery_service.add_product_images(
            self.product,
            [img1, img2],
            alt_texts=['Angle 1', 'Angle 2'],
        )
        self.assertEqual(len(created), 2)
        self.assertTrue(created[0].is_primary)
        self.assertFalse(created[1].is_primary)

        # Set second image as primary
        gallery_service.set_primary_image(self.product, created[1].id)
        created[0].refresh_from_db()
        created[1].refresh_from_db()
        self.assertFalse(created[0].is_primary)
        self.assertTrue(created[1].is_primary)

    def test_cart_item_duplicate_constraint(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)

        with self.assertRaises(IntegrityError):
            CartItem.objects.create(cart=cart, product=self.product, quantity=2)

    def test_health_check_endpoint(self):
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['database'], 'connected')
