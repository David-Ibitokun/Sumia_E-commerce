# Project Structure

## Overview

The **Sumia** e-commerce platform is a Django web application split into four
apps. Each app owns one area of the domain, keeps its views in a small package
grouped by feature, and puts its business logic in a service layer instead of
inside the views.

| App | Responsibility |
|-----|----------------|
| `pages` | Shared domain models (catalog, cart, orders) and public pages |
| `shop` | Storefront, cart, checkout, wishlist, search, vendor tools |
| `authentications` | Custom user model, login/logout, registration, dashboards |
| `sumia` | Project settings, root URLconf and WSGI/ASGI entry points |

## Directory Layout

```
.
├── authentications/            # Accounts, roles and dashboards
│   ├── admin.py
│   ├── forms.py                # Registration and login forms
│   ├── models.py               # UsersRegistration (AUTH_USER_MODEL)
│   ├── urls.py
│   └── views.py
├── docs/                       # scope.md, project_structure.md
├── manage.py
├── media/                      # Uploaded product and brand images
├── pages/                      # Domain models + public pages
│   ├── admin.py
│   ├── apps.py                 # Connects the cache invalidation signals
│   ├── context_processors.py   # Cached navigation category tree
│   ├── management/commands/    # populate_categories
│   ├── models.py               # Category, Brand, Product, Cart, Wishlist, Order
│   ├── migrations/
│   ├── signals.py              # Invalidates the category tree cache
│   ├── templatetags/
│   ├── tests.py
│   ├── urls.py
│   └── views/
│       ├── account.py          # my_account
│       └── public.py           # home, about, contact, error pages
├── shop/                       # Everything the storefront needs
│   ├── forms.py                # ProductForm, CheckoutForm
│   ├── services/               # Business logic, no HTTP involved
│   │   ├── cart.py             # Cart mutations, totals, stock rules
│   │   ├── catalog.py          # Product queries, related items, search
│   │   ├── categories.py       # Category tree: descendants, breadcrumbs
│   │   ├── exceptions.py       # Domain errors the views translate to messages
│   │   ├── orders.py           # Atomic order placement, order queries
│   │   └── wishlist.py         # Wishlist mutations and counts
│   ├── tests.py
│   ├── urls.py
│   └── views/
│       ├── ajax.py             # JSON endpoints for ajax_ecommerce.js
│       ├── cart.py             # Cart page and cart mutations
│       ├── catalog.py          # Vendor product CRUD
│       ├── checkout.py         # Shipping form and order placement
│       ├── orders.py           # Customer order history
│       ├── public.py           # Shop, product, category, brand pages
│       ├── search.py           # Search results page
│       ├── utils.py            # redirect_back, json_error
│       ├── vendors.py          # Vendor scoped order views
│       └── wishlist.py         # Wishlist page and mutations
├── static/
│   └── js/ajax_ecommerce.js    # Progressive enhancement for cart/wishlist/search
├── sumia/                      # Django project package
│   ├── settings.py
│   └── urls.py                 # Root routes and error handlers
├── templates/                  # All templates, grouped by the area they serve
│   ├── base.html               # The only shared layout; every page extends it
│   ├── accounts/               # Authentication and account screens
│   │   ├── login.html
│   │   ├── my_account.html
│   │   ├── my_profile.html
│   │   ├── register.html
│   │   └── user_dashboard.html
│   ├── catalog/                # Browsing: everything a shopper can look at
│   │   ├── brand_detail.html
│   │   ├── brand_list.html
│   │   ├── category_detail.html
│   │   ├── product_detail.html
│   │   ├── search_results.html
│   │   ├── shop.html
│   │   └── wishlist.html
│   ├── checkout/               # cart, checkout
│   ├── errors/                 # 404, 500, 503
│   ├── orders/                 # order_list, order_detail
│   ├── pages/                  # index, about, contact
│   └── vendor/
│       ├── add_product.html
│       ├── dashboard.html
│       ├── delete_product_confirm.html
│       ├── edit_product.html
│       ├── order_detail.html
│       ├── orders.html
│       ├── partials/           # Fragments shared by the product forms
│       │   └── category_selector.html
│       └── product_list.html
├── requirements.txt
├── run_server.bat
└── venv/
```

## Template Conventions

- **One directory per area, name after the view.** A view called `order_list`
  renders `orders/order_list.html`; `edit_product` renders
  `vendor/edit_product.html`. There are no historical names such as
  `recent_orders.html` or `myAccount.html` left in the tree.
- **`base.html` is the only shared layout.** Every page extends it and fills the
  `content` block; markup shared between two pages becomes a partial under
  `partials/` (currently only `vendor/partials/category_selector.html`).
- **Templates stay dumb.** They format context that a view prepared; a template
  never walks the category tree or recomputes a total.

## Architecture Notes

### Views are thin, services hold the rules
A view resolves the request, calls one or two service functions and renders the
result. Rules such as "how many units of a product may be added" live once in
`shop/services/cart.py` instead of being duplicated between the HTML form view
and the AJAX view.

### Domain errors instead of blanket `except Exception`
Services raise `InvalidQuantityError`, `OutOfStockError`,
`ProductUnavailableError` and `InsufficientStockError` (all subclasses of
`ShopServiceError`). Views catch `ShopServiceError` and turn it into a message,
so a real database or programming error is no longer swallowed.

### Order placement is atomic
`shop.services.orders.create_order` locks and decrements stock, snapshots prices
onto `OrderItem` and clears the cart inside one transaction. A failure leaves the
cart untouched and no half-placed order behind.

### Forms own validation
`CheckoutForm` validates the shipping and payment fields (including refusing
payment methods the storefront has not integrated yet) and returns the cleaned
values through `shipping_data()`. `ProductForm` already provides the `category`
field, so views no longer read it out of `request.POST` by hand.

### Category queries run once
- The navigation tree is cached in `pages.context_processors` and invalidated
  by `pages.signals` whenever a category is saved or deleted.
- The subtree of a category is read with a single query and walked in memory
  (`shop.services.categories.descendant_ids`) instead of one recursive query per
  level, per request.
- Breadcrumbs are built from categories fetched with `select_related` parents,
  and listings use `select_related` for category and brand.
- `shop.views.catalog.category_selection` resolves which category and which
  top level panel the vendor form should open, so re-rendering a form after a
  validation error no longer loses the shopper's pick.

### Consistent naming
Views, functions, URL names and template files are `snake_case`
(`my_account` → `accounts/my_account.html`, `product_detail` →
`catalog/product_detail.html`, `order_list` → `orders/order_list.html`). Two
legacy route names remain as aliases for older bookmarks: `singleProduct`
(`/products/<slug>/`) and `myAccount` (`/myAccount/`).

## Development Flow

1. **Clone** → `git clone <repo>`
2. **Virtual Environment** → `python -m venv venv`
3. **Install Dependencies** → `pip install -r requirements.txt`
4. **Apply Migrations** → `python manage.py migrate`
5. **Seed categories** (optional) → `python manage.py populate_categories`
6. **Create Superuser** → `python manage.py createsuperuser`
7. **Run Tests** → `python manage.py test`
8. **Run Server** → `python manage.py runserver`
