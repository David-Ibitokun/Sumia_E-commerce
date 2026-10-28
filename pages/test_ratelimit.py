"""Tests for Token Bucket Rate Limiting."""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.http import HttpResponse

from pages.ratelimit import TokenBucket, ratelimit

User = get_user_model()


class TokenBucketUnitTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.bucket = TokenBucket(capacity=3, refill_rate=1.0, key_prefix='test_bucket')

    def test_consume_within_capacity(self):
        # 3 requests allowed immediately
        allowed1, remaining1, _ = self.bucket.consume('client_1')
        allowed2, remaining2, _ = self.bucket.consume('client_1')
        allowed3, remaining3, _ = self.bucket.consume('client_1')

        self.assertTrue(allowed1)
        self.assertTrue(allowed2)
        self.assertTrue(allowed3)
        self.assertLess(remaining3, 0.05)

        # 4th request must be rejected
        allowed4, _, retry_after = self.bucket.consume('client_1')
        self.assertFalse(allowed4)
        self.assertGreater(retry_after, 0.0)

    def test_bucket_refills_over_time(self):
        # Drain all 3 tokens
        for _ in range(3):
            self.bucket.consume('client_2')

        # Initially empty
        allowed, _, _ = self.bucket.consume('client_2')
        self.assertFalse(allowed)

        # Simulate time passing by manually updating cache state
        cache_key = 'test_bucket:client_2'
        tokens, last_time = cache.get(cache_key)
        # Advance time by 2 seconds = 2 tokens refilled
        cache.set(cache_key, (tokens, last_time - 2.0))

        # Should now be allowed
        allowed_after, remaining_after, _ = self.bucket.consume('client_2')
        self.assertTrue(allowed_after)


class RateLimitDecoratorTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    def test_ratelimit_decorator_html(self):
        @ratelimit(capacity=2, refill_rate=0.5, key_prefix='test_view')
        def sample_view(request):
            return HttpResponse("OK")

        req1 = self.factory.get('/test/')
        res1 = sample_view(req1)
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1['X-RateLimit-Limit'], '2')

        req2 = self.factory.get('/test/')
        res2 = sample_view(req2)
        self.assertEqual(res2.status_code, 200)

        # 3rd request should return 429
        req3 = self.factory.get('/test/')
        res3 = sample_view(req3)
        self.assertEqual(res3.status_code, 429)
        self.assertIn('Retry-After', res3)

    def test_ratelimit_decorator_json(self):
        @ratelimit(capacity=1, refill_rate=0.1, key_prefix='test_api', is_json=True)
        def sample_json_view(request):
            return HttpResponse("OK")

        req1 = self.factory.get('/test-api/')
        res1 = sample_json_view(req1)
        self.assertEqual(res1.status_code, 200)

        # 2nd request should return 429 JSON
        req2 = self.factory.get('/test-api/')
        res2 = sample_json_view(req2)
        self.assertEqual(res2.status_code, 429)
        self.assertEqual(res2.headers.get('Content-Type'), 'application/json')
