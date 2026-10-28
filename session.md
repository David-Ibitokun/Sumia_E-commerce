# Project Session Log

**Current Goal:** Execute on the project backlog to bring the Sumia application to complete, production-ready, portfolio-grade quality.

---

## Session Overview
- **Session Started:** 2026-10-28
- **Status:** All core milestones in the backlog completed and verified. Fixed Django CheckConstraint backward compatibility.

---

## Log of Activities

### 2026-10-28
- **Audit & Backlog Initialization:**
  - Reviewed project architecture, services, views, and documentation (`FEATURE_IMPLEMENTATION.md`, `improvements.md`, `docs/scope.md`).
  - Created [`backlog.md`](backlog.md) and [`session.md`](session.md).
  - Executed existing test suite: verified all 57 existing unit tests pass without errors.
- **Authorization & Data Isolation Audit:**
  - Audited `shop/views/catalog.py`, `shop/views/vendors.py`, and `authentications/views.py`.
  - Confirmed vendor ownership verification and multi-vendor order isolation (`orders_for_vendor`, `vendor_order_items`, `get_vendor_order`).
  - Checked `run_server.bat` and confirmed no machine-specific absolute file paths are present.
- **Database Model Enhancements & Constraints:**
  - Added `ProductReview` model with rating choices (1-5), verified purchase tracking, approval flag, and unique constraints.
  - Added `ProductImage` gallery model with primary toggle and ordering.
  - Added check constraints:
    - `product_price_non_negative` on `Product`.
    - `product_stock_non_negative` on `Product`.
    - `cart_item_quantity_positive` on `CartItem`.
    - `unique_product_per_cart` unique constraint on `CartItem`.
  - Updated `CheckConstraint` parameter from `condition=` (Django 5.1+ only) to `check=` (Django 4.2 LTS / 5.x cross-compatible) in both [`pages/models.py`](pages/models.py) and migration `0004`.
- **Service Layer & Admin Updates:**
  - Created [`shop/services/reviews.py`](shop/services/reviews.py) for review creation, verified purchase checking, and aggregated rating statistics.
  - Created [`shop/services/gallery.py`](shop/services/gallery.py) for gallery management.
  - Registered `ProductReview` and `ProductImage` in [`pages/admin.py`](pages/admin.py) with moderation actions.
- **Storefront & Review UI Integration:**
  - Created [`shop/views/reviews.py`](shop/views/reviews.py) and added `/product/<int:product_id>/review/` route.
  - Updated `product_detail` view in [`shop/views/public.py`](shop/views/public.py) to supply reviews, stats, and review form.
  - Updated [`templates/catalog/product_detail.html`](templates/catalog/product_detail.html) with:
    - Rating summary badge in product header.
    - Full customer review section with 5-star progress bars, verified purchase badges, and review submission form.
- **Frontend & Modern UI Components Overhaul:**
  - **Dark / Light Mode**:
    - Created `static/css/dark-mode.css` with dark theme palette and transitions.
    - Created `static/js/dark-mode.js` persisting preference in `localStorage`.
    - Added theme toggle button into header navbar across all templates.
  - **Interactive Product Quick View Modal**:
    - Created `ajax_quick_view` endpoint in `shop/views/ajax.py` and `shop/urls.py`.
    - Created `templates/partials/quick_view_modal.html` included globally via `base.html`.
    - Added `static/js/quick-view.js` client logic to fetch and display modal data with direct AJAX cart addition.
    - Added Quick View action buttons to product cards in `shop.html` and `index.html`.
  - Ran `collectstatic` to sync all updated static assets.
- **Deployment Hardening & Production Containerization:**
  - Added `gunicorn` and `psycopg2-binary` to [`requirements.txt`](requirements.txt).
  - Created [`Procfile`](Procfile) for standard WSGI execution on PaaS.
  - Created multi-stage production [`Dockerfile`](Dockerfile) with automated migration, unbuffered Python logging, and Gunicorn workers.
  - Created [`docker-compose.yml`](docker-compose.yml) bundle with PostgreSQL 16 Alpine container and health checks.
  - Untracked `db.sqlite3` and empty `datadump.json` from git index to prevent committing local databases.
  - Verified `python manage.py check --deploy` passes with **0 silenced, 0 issues**.
- **Token Bucket Rate Limiting:**
  - Implemented [`pages/ratelimit.py`](pages/ratelimit.py) containing `TokenBucket` class and `@ratelimit` decorator backed by Django's cache framework.
  - Applied rate limiting across sensitive endpoints:
    - `login_user` (burst 5, refill 0.1 tokens/sec).
    - `register_user` (burst 10, refill 0.2 tokens/sec).
    - `checkout` (burst 10, refill 0.5 tokens/sec).
    - `ajax_search` (burst 30, refill 5.0 tokens/sec, JSON responses).
  - Added [`pages/test_ratelimit.py`](pages/test_ratelimit.py) and verified all 4 tests pass (**4/4 OK**).
- **Deployment Database Seeder Script (`seed_db.py`):**
  - Created idempotent standalone script [`seed_db.py`](seed_db.py) to seed initial superuser, demo vendor/customer, categories, brands, products with images/tags, and product reviews.
  - Verified execution under both virtualenv (Django 4.2 LTS) and global environment.
  - Hooked into [`build.sh`](build.sh) and [`Dockerfile`](Dockerfile).
- **Dark Mode Browser Automated Audit & Polish:**
  - Automated browser testing executed with Playwright against live server at `http://127.0.0.1:8000` using vendor credentials `vendor_account:pass0987`.
  - Identified and fixed critical dark mode flaws:
    - Overhauled [`static/css/dark-mode.css`](static/css/dark-mode.css) with high-contrast surfaces, readable text, and borders.
    - Fixed `.sumia-nav-bar`, `.sumia-topbar`, and `.sumia-footer` background color inheritance.
    - Styled `.btn-outline-dark`, `.btn-dark`, `.btn-light`, and `.btn-warning` for dark mode.
    - Updated table headers (`<thead class="table-light">`) to dark surface `#0f172a` with `#94a3b8` text.
    - Re-styled vendor stat cards, badge contrasts, and alert banners in [`templates/vendor/dashboard.html`](templates/vendor/dashboard.html).
    - Fixed user avatar badge letter contrast in [`templates/base.html`](templates/base.html).
  - Executed automated contrast verification: **0 light background failures and 0 contrast issues (<3.0:1)** across Homepage, Vendor Dashboard, Shop, Vendor Orders, Vendor Products, and Product Detail.
- **Selection & Input Highlight Polish:**
  - Resolved low-contrast text selection highlight (`::selection`) where white text rendered on pale yellow background.
  - Standardized `::selection` to high-contrast brand amber `#f59e0b` background with dark slate `#0b1120` text (WCAG AAA contrast ratio > 10:1).
  - Added dark mode input field background (`#0f172a`), amber focus borders, and `-webkit-autofill` dark overrides across auth forms ([`authentications/static/authentications/css/auth-styles.css`](authentications/static/authentications/css/auth-styles.css), [`static/css/dark-mode.css`](static/css/dark-mode.css)).
  - Verified with Playwright screenshot `login_highlight_dark.png`.

- **WebP Image Pipeline & Storage Optimization:**
  - Implemented automatic conversion of uploaded product images, gallery images, and brand logos to WebP format with EXIF orientation correction and dimension clamping (max 1600px).
  - Preserved alpha transparency for RGBA assets and reduced payload sizes.
  - Added test suite in [pages/tests.py](pages/tests.py) verifying conversion across models.
- **Search UI & Search Ranking Algorithm Overhaul:**
  - Modernized search ranking in [shop/services/catalog.py](shop/services/catalog.py) with weighted multi-token evaluation and relevance scoring across name, brand, category, tags, and descriptions.
  - Added multi-column sorting (
elevance, price_asc, price_desc, 
ewest) across catalog and full search results page.
  - Redesigned AJAX live search dropdown in [static/js/ajax_ecommerce.js](static/js/ajax_ecommerce.js), [static/css/custom-theme.css](static/css/custom-theme.css), and [static/css/dark-mode.css](static/css/dark-mode.css) with matched dark/light palette, query highlighting, thumbnail previews, keyboard navigation (ArrowUp/Down/Enter/Escape), and dark footer.
  - Verified full test suite: **83/83 tests passing**.

- **Mobile Responsiveness & Dark Mode Polish:**
  - Resolved dark mode initialization sync: added pre-render <head> theme injector in [	emplates/base.html](templates/base.html) to prevent flash of light theme or state desync between pages.
  - Unified localStorage key binding in [static/js/dark-mode.js](static/js/dark-mode.js) to support both sumia-theme and 	heme seamlessly.
  - Eliminated hardcoded light inline gradients across [	emplates/pages/about.html](templates/pages/about.html), [	emplates/catalog/brand_detail.html](templates/catalog/brand_detail.html), [	emplates/catalog/brand_list.html](templates/catalog/brand_list.html), and [	emplates/catalog/category_detail.html](templates/catalog/category_detail.html) with .sumia-cta-banner and themed dark radial gradient.
  - Fixed mobile responsive breakage in Vendor Navigation (.vendor-pill-nav): converted rigid pill to flex-wrapped pill-badge grid on small viewports with dark surface #1e293b.
  - Fixed mobile card truncation in Vendor Dashboard metric cards: changed grid from col-6 to col-12 col-sm-6 col-lg-3 with overflow-hidden and text protection.
  - Verified visual output across mobile (375x812) viewports via Playwright screenshots.

- **Firefox JavaScript Guard & Theme Persistence Resolution:**
  - Resolved JavaScript uncaught ReferenceError: jarallax is not defined and Chocolat is not defined inside [static/js/script.js](static/js/script.js) that halted execution of subsequent scripts in Firefox.
  - Reordered script includes in [	emplates/base.html](templates/base.html) so [static/js/dark-mode.js](static/js/dark-mode.js) initializes independently before third-party vendor scripts.
  - Added dual target pplyTheme() setting data-theme on both document.documentElement and document.body for robust selector matching across all rendering engines.

- **Navigation Pill Layout Constraint (width: max-content;):**
  - Updated .sumia-nav-bar .nav-link across [static/css/custom-theme.css](static/css/custom-theme.css) and [static/css/dark-mode.css](static/css/dark-mode.css) with width: max-content; and white-space: nowrap;.
  - Prevents active background pills and nav text from wrapping, expanding or going out of place across responsive breakpoints and browser engines.
  - Ran collectstatic and verified computed CSS properties.
- **Search Header Default Category Fix:**
  - Resolved template conditional in [templates/base.html](templates/base.html) where category filter comparison evaluated to truthy on empty string, causing the final option in the loop to be marked selected by default.
  - Replaced with string comparison `request.GET.category and request.GET.category == parent.id|stringformat:"s"`, ensuring `<option value="" selected>All Categories</option>` is correctly chosen by default on all page loads.
