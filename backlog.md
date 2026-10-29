# Project Backlog

This backlog tracks the complete roadmap for the Sumia E-Commerce platform across architecture, feature delivery, tests, performance, security, and operations.

---

## Status Legend
- `[ ]` Pending
- `[-]` In Progress
- `[x]` Completed

---

## 1. Authorization & Role Hardening
- [x] Verify vendor-only restrictions across all vendor dashboard views (`shop/views/vendors.py`, `shop/views/catalog.py`).
- [x] Enforce vendor ownership checks so vendors cannot edit or delete products owned by other vendors (`shop/views/catalog.py`).
- [x] Enforce multi-vendor isolation on vendor order details: ensure a vendor can only view line items for products they own (`shop/services/orders.py`).
- [x] Customer privacy: ensure customers can only view their own orders and account details.
- [x] Clean up local hardcoded paths in scripts (`run_server.bat` verified sanitized).

---

## 2. Customer-Facing Features
- [x] **Product Reviews and Ratings**:
  - [x] Implement `ProductReview` model (rating 1-5, title, comment, verified purchase, approval status) in `pages/models.py`.
  - [x] Implement review submission form and service (`create_review`, `get_product_rating_stats`) in `shop/services/reviews.py`.
  - [x] Integrate reviews and rating distribution into `templates/catalog/product_detail.html`.
  - [x] Register `ProductReview` in Django Admin (`pages/admin.py`) with moderation actions.
- [x] **Product Image Gallery & Variants**:
  - [x] Support secondary product images (`ProductImage` gallery model) in `pages/models.py`.
  - [x] Implement image management services (`add_product_images`, `reorder_images`, `set_primary_image`) in `shop/services/gallery.py`.
  - [x] Register `ProductImage` in Django Admin (`pages/admin.py`).
- [x] **Order Tracking & Notifications**:
  - [x] Verified existing order status pipeline (`pending`, `processing`, `shipped`, `delivered`, `cancelled`).

---

## 3. Frontend & Modern Interactive UI Components
- [x] **Dark / Light Mode**:
  - [x] Created `static/css/dark-mode.css` with dark theme palette and transitions.
  - [x] Created `static/js/dark-mode.js` persisting preference in `localStorage`.
  - [x] Integrated theme toggle button into header navbar across all pages.
  - [x] Conducted full automated browser audit with Playwright (`vendor_account` credentials).
  - [x] Resolved all contrast issues and light background inheritance across topbar, navbar, footer, cards, tables, vendor dashboard, buttons, and badges (achieving 0 contrast errors).
  - [x] Fixed text selection & autofill highlight colors (`::selection`, `input::selection`, `:-webkit-autofill`) to ensure high contrast (#f59e0b highlight with #0b1120 text).
- [x] **Interactive Product Quick View Modal**:
  - [x] Backend endpoint `ajax_quick_view` in `shop/views/ajax.py` and route in `shop/urls.py`.
  - [x] Created reusable modal partial `templates/partials/quick_view_modal.html`.
  - [x] Interactive client controller in `static/js/quick-view.js`.
  - [x] Integrated quick-view action buttons into product cards in `shop.html` and `index.html`.
- [x] Compiled static assets using `collectstatic`.

---

## 4. Rate Limiting (Token Bucket)
- [x] Implemented `TokenBucket` rate limiter engine and `@ratelimit` decorator in [`pages/ratelimit.py`](pages/ratelimit.py).
  - Cache-backed continuous token refill based on elapsed time and burst capacity.
  - Supports client identification via authenticated user or IP (with proxy header support).
  - Rejection with HTTP 429 Too Many Requests, `Retry-After` header, and rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`).
- [x] Applied rate limits across sensitive routes:
  - User Login (`capacity=5`, `refill_rate=0.1`).
  - User Registration (`capacity=10`, `refill_rate=0.2`).
  - Order Checkout (`capacity=10`, `refill_rate=0.5`).
  - AJAX Product Search (`capacity=30`, `refill_rate=5.0`, `is_json=True`).
- [x] Added automated unit tests in [`pages/test_ratelimit.py`](pages/test_ratelimit.py) (**4/4 passing**).

---

## 5. Production Readiness & Deployment Configuration
- [x] **Database Seeding (`seed_db.py`)**:
  - [x] Standalone idempotent script to seed initial superuser, demo vendor/customer, categories, brands, products, and customer reviews.
  - [x] Integrated into [`build.sh`](build.sh) and [`Dockerfile`](Dockerfile).
- [x] **Production WSGI & Server**:
  - [x] Added `gunicorn` and `psycopg2-binary` to [`requirements.txt`](requirements.txt).
  - [x] Created [`Procfile`](Procfile) for PaaS platforms (Heroku, Render, Railway).
  - [x] Created production [`Dockerfile`](Dockerfile) with multi-stage build, unbuffered logging, and gunicorn entrypoint.
  - [x] Created [`docker-compose.yml`](docker-compose.yml) with PostgreSQL service and healthcheck.
  - [x] Updated [`build.sh`](build.sh) for one-step deployment migration and static compilation.
- [x] **Deployment Security Checklist**:
  - [x] Passed `python manage.py check --deploy` with 0 issues identified.
  - [x] Untracked `db.sqlite3` and empty `datadump.json` from git repository.
  - [x] Verified `.env` and `staticfiles_collected` are properly ignored by `.gitignore`.

---

## 6. Automated Testing Suite
- [x] Verified test suite (**68 tests passing** across `shop.tests`, `shop.test_features`, and `pages.test_ratelimit`).

## Completed Deliverables
- [x] Automatic WebP image conversion for all image uploads (Product.image, Brand.logo, ProductImage.image).
- [x] Search ranking algorithm upgrade with relevance scoring, token matching, and multi-criteria sorting.
- [x] Live search dropdown redesign with theme matching, keyboard navigation, and dark footer.
- [x] Mobile Responsiveness & Dark Mode Polish: Fixed vendor pill navigation wrapping, metric cards responsive grid (col-12 col-sm-6), pre-render theme script, and .sumia-cta-banner dark mode styles.

---

## 7. Production Hardening, Authentication Flow & XSS Prevention
- [x] **Production Deployment Gating**:
  - [x] Gated `seed_db.py` in [`build.sh`](build.sh) and [`Dockerfile`](Dockerfile) behind explicit `DJANGO_SEED_DB=true` flag to prevent unauthorized demo credentials in production.
  - [x] Hardened Docker container to run as unprivileged `appuser` (UID 1000) with container `HEALTHCHECK` probe against `/health/`.
  - [x] Synchronized [`requirements.txt`](requirements.txt) to `Django>=5.2.0,<6.0.0` and added `bleach>=6.1.0`.
- [x] **Authentication Flow Best Practices**:
  - [x] **Open Redirect Defense**: Validated post-login `next` destination using `url_has_allowed_host_and_scheme` in [`authentications/views.py`](authentications/views.py) and added hidden input to [`login.html`](templates/accounts/login.html).
  - [x] **Logout CSRF Protection**: Replaced vulnerable GET logout link in [`base.html`](templates/base.html) with CSRF-tokenized POST form action; updated [`logout_user`](authentications/views.py) to support secure POST with graceful GET fallback.
  - [x] **Account Collision Prevention**: Added `clean_email()` uniqueness checks to both `UsersRegistrationForm` and `ProfileForm` in [`authentications/forms.py`](authentications/forms.py).
  - [x] **Self-Service Password Reset**: Configured Django's password reset views and created 5 brand-styled recovery templates in [`templates/accounts/`](templates/accounts/).
- [x] **Cross-Site Scripting (XSS) Prevention**:
  - [x] Created [`SecurityHeadersMiddleware`](sumia/middleware.py) injecting `Content-Security-Policy`, `X-XSS-Protection: 1; mode=block`, `X-Content-Type-Options: nosniff`, and `Permissions-Policy`.
  - [x] Explicitly enforced `SESSION_COOKIE_HTTPONLY = True` to shield session keys from malicious client-side script access.
  - [x] Integrated `bleach` sanitization in [`shop/forms.py`](shop/forms.py) (`ReviewForm`) to strip executable markup from customer reviews.
  - [x] Added automated test coverage in [`authentications/tests.py`](authentications/tests.py) (**17/17 passing**).
- [x] **OpenAPI 3.0 & Swagger UI Integration**:
  - [x] Added `djangorestframework>=3.15.0` and `drf-spectacular>=0.28.0` to [`requirements.txt`](requirements.txt).
  - [x] Configured `SPECTACULAR_SETTINGS` in [`sumia/settings.py`](sumia/settings.py).
  - [x] Implemented OpenAPI schema generator (`/api/schema/`), interactive Swagger UI (`/api/docs/`), and ReDoc (`/api/redoc/`) in [`sumia/urls.py`](sumia/urls.py).
  - [x] Added REST API serializers, views, and routing for storefront products, categories, and brands in [`shop/api_urls.py`](shop/api_urls.py).
  - [x] Added automated test coverage in [`shop/test_api.py`](shop/test_api.py) (**7/7 passing**).
- [x] **Redis Integration for Production Caching & Rate Limiting**:
  - [x] Added `redis>=5.0.0` to [`requirements.txt`](requirements.txt).
  - [x] Configured `CACHES` in [`sumia/settings.py`](sumia/settings.py) using `django.core.cache.backends.redis.RedisCache` when `REDIS_URL` is set, with graceful fallback to `LocMemCache`.
  - [x] Configured `SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'` for Redis session caching with PostgreSQL durability.
  - [x] Added Redis 7 container service with healthchecks and persistent volume to [`docker-compose.yml`](docker-compose.yml).
  - [x] Updated [`health_check`](pages/views/public.py) to probe cache connectivity alongside database status.
