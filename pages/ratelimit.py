"""Token Bucket Rate Limiting implementation for Django.

Implements the standard Token Bucket algorithm using Django's caching framework:
- Each client (IP address or authenticated user) has a bucket with a maximum capacity.
- Tokens refill continuously over time at a specified rate (tokens per second).
- Each request consumes 1 (or more) tokens.
- If tokens are available, the request proceeds and remaining tokens are decremented.
- If the bucket is empty, the request is rejected with HTTP 429 Too Many Requests
  and a 'Retry-After' header indicating when enough tokens will be refilled.
"""
import time
from functools import wraps
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse


class TokenBucket:
    """Token Bucket rate limiter backed by Django cache."""

    def __init__(self, capacity: int, refill_rate: float, key_prefix: str = 'rl'):
        """
        :param capacity: Maximum number of tokens the bucket can hold (burst limit).
        :param refill_rate: Number of tokens added to the bucket per second.
        :param key_prefix: Cache key namespace.
        """
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.key_prefix = key_prefix
        # TTL for cache key: time it takes to refill an empty bucket to full capacity + buffer
        self.ttl = int(self.capacity / self.refill_rate) + 60 if self.refill_rate > 0 else 300

    def get_client_identifier(self, request) -> str:
        """Derive client identifier: authenticated user ID or remote IP."""
        if getattr(request, 'user', None) and request.user.is_authenticated:
            return f"user:{request.user.id}"
        
        # Check X-Forwarded-For if behind a proxy
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            ip = x_forwarded.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return f"ip:{ip}"

    def consume(self, client_id: str, tokens: float = 1.0):
        """
        Attempt to consume `tokens` from the bucket for `client_id`.
        Returns a tuple: (allowed: bool, remaining_tokens: float, retry_after_seconds: float)
        """
        now = time.time()
        cache_key = f"{self.key_prefix}:{client_id}"
        state = cache.get(cache_key)

        if state is None:
            # First request: bucket starts full
            current_tokens = self.capacity
            last_updated = now
        else:
            current_tokens, last_updated = state
            # Refill tokens based on elapsed time
            elapsed = max(0.0, now - last_updated)
            current_tokens = min(self.capacity, current_tokens + (elapsed * self.refill_rate))
            last_updated = now

        if current_tokens >= tokens:
            # Request allowed
            current_tokens -= tokens
            cache.set(cache_key, (current_tokens, last_updated), timeout=self.ttl)
            return True, current_tokens, 0.0
        else:
            # Request rate limited
            deficit = tokens - current_tokens
            retry_after = deficit / self.refill_rate if self.refill_rate > 0 else 1.0
            # Save current state without decrementing
            cache.set(cache_key, (current_tokens, last_updated), timeout=self.ttl)
            return False, current_tokens, max(1.0, retry_after)


def ratelimit(capacity: int = 60, refill_rate: float = 1.0, key_prefix: str = 'rl', is_json: bool = False):
    """
    Decorator to apply Token Bucket rate limiting to a view function.

    :param capacity: Burst capacity (e.g. 5 requests for login, 30 for search).
    :param refill_rate: Tokens added per second (e.g. 0.2 tokens/sec = 1 per 5 seconds).
    :param key_prefix: Namespace for the rate limit rule.
    :param is_json: If True, returns a JSON error response instead of HTML.
    """
    bucket = TokenBucket(capacity=capacity, refill_rate=refill_rate, key_prefix=key_prefix)

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            client_id = bucket.get_client_identifier(request)
            allowed, remaining, retry_after = bucket.consume(client_id)

            if not allowed:
                retry_int = int(retry_after) + 1
                if is_json or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    response = JsonResponse({
                        'status': 'error',
                        'message': 'Too many requests. Please slow down.',
                        'retry_after': retry_int,
                    }, status=429)
                else:
                    content = (
                        f"<!DOCTYPE html><html><head><title>Too Many Requests</title></head>"
                        f"<body style='font-family: sans-serif; text-align: center; padding: 50px;'>"
                        f"<h1>429 - Too Many Requests</h1>"
                        f"<p>You are making requests too quickly. Please try again in {retry_int} seconds.</p>"
                        f"</body></html>"
                    )
                    response = HttpResponse(content, status=429)

                response['Retry-After'] = str(retry_int)
                return response

            response = view_func(request, *args, **kwargs)
            # Add rate limit headers to response
            response['X-RateLimit-Limit'] = str(int(bucket.capacity))
            response['X-RateLimit-Remaining'] = str(int(remaining))
            return response

        return wrapper
    return decorator
