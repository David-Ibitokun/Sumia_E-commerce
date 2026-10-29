"""Security Middleware for Sumia E-Commerce.

Enforces defensive HTTP response headers to protect against:
- Cross-Site Scripting (XSS) via Content-Security-Policy and X-XSS-Protection.
- MIME-sniffing attacks via X-Content-Type-Options.
- Clickjacking via frame-ancestors / X-Frame-Options.
- Unnecessary hardware API access via Permissions-Policy.
"""
import os


class SecurityHeadersMiddleware:
    """Middleware that injects Content Security Policy and modern security headers."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.csp_enabled = os.environ.get('CSP_ENABLED', 'True').lower() == 'true'

        # Default CSP directives allowing required CDNs (Bootstrap, Swiper, FontAwesome, Google Fonts)
        self.csp_header = os.environ.get(
            'CONTENT_SECURITY_POLICY',
            (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
                "img-src 'self' data: https: blob:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        )

    def __call__(self, request):
        response = self.get_response(request)

        # Content-Security-Policy (XSS prevention)
        if self.csp_enabled and 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = self.csp_header

        # MIME-sniffing prevention
        if 'X-Content-Type-Options' not in response:
            response['X-Content-Type-Options'] = 'nosniff'

        # Legacy XSS protection header for older browsers
        if 'X-XSS-Protection' not in response:
            response['X-XSS-Protection'] = '1; mode=block'

        # Restrict dangerous browser features
        if 'Permissions-Policy' not in response:
            response['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=(), payment=()'

        return response
