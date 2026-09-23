# Project Structure

## Overview

The **Sumia** e-commerce platform is a Django-based web application organized into several modular Python packages and template directories.

## Directory Layout

```
.
├── .git/                    # Git repository
├── .kilo/                   # Worktree snapshots (alternate versions)
├── authentications/         # User authentication & authorization
│   ├── models.py            # User and vendor models
│   ├── forms.py             # Authentication forms
│   ├── urls.py              # Auth routes
│   └── views.py             # Authentication views
├── data.json                # Application data (catalog, etc.)
├── deployment.yaml          # Deployment configuration
├── docs/                    # Documentation
│   ├── scope.md            # Project scope definition
│   └── project_structure.md # This file
├── fixtures/                # Test fixtures
├── manage.py               # Django command-line utility
├── migration.bat           # Migration helper script
├── markdown/               # Markdown assets (if any)
├── requirements.txt         # Python dependencies
├── run_server.bat          # Server startup script
├── schemas/                 # Data schemas (if any)
├── static/                  # Static files (CSS, JS, images)
├── templates/               # Base templates and page templates
│   ├── base.html           # Master layout
│   ├── index.html          # Home page
│   ├── shop.html           # Main shop view
│   ├── product_detail.html # Individual product view
│   ├── category_detail.html# Category detail page
│   ├── cart.html           # Shopping cart
│   ├── login.html          # Authentication page
│   ├── register.html       # User registration
│   ├── checkout.html       # Order placement
│   ├── vendor_dashboard.html # Vendor management
│   └── ... (more templates)
├── pages/                   # Page-level views (custom pages)
│   ├── admin.py            # Admin site configuration
│   ├── apps.py             # App registry
│   ├── context_processors.py
│   ├── management/
│   │   └── commands/
│   ├── models.py           # Shared models
│   ├── templates/
│   │   ├── admin.py        # Admin templates
│   │   ├── product_list.html
│   │   ├── brand_detail.html
│   │   ├── cart.html
│   │   ├── order_detail.html
│   │   └── ...
│   ├── templatetags/
│   └── tests.py
├── sumia/                  # Main Django application package
│   ├── __init__.py
│   ├── asgi.py             # ASGI entry point
│   ├── settings.py         # Django settings
│   ├── urls.py             # Root URL routing
│   ├── wsgi.py             # WSGI entry point
│   ├── apps.py             # App registry
│   ├── models.py           # Core models (User, Product, Category, etc.)
│   ├── views.py            # Generic views
│   ├── management/
│   │   └── commands/
│   └── templates/          # App-specific templates
│       ├── base.html
│       ├── shop.html
│       ├── product_detail.html
│       ├── category_detail.html
│       ├── cart.html
│       ├── order_detail.html
│       └── ...
├── shop/                    # Shop-specific functionality
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── forms.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
├── authentications/        # Repeated auth module (shared)
├── STYLING_GUIDE.md        # CSS/UI styling guidelines
├── verification/           # Verification scripts (if any)
└── scripts/                # Utility scripts
    ├── populate_categories.bat
    ├── generate_inventory.bat
    └── ...
```

## Key Components

### 1. **Core Applications**
- **`sumia/`** – Main Django project package containing:
  - `models.py` – Core domain models (User, Product, Category, Order, etc.)
  - `views.py` – Business logic and HTTP response handling
  - `urls.py` – Route definitions
  - `settings.py` – Configuration (database, static files, third-party services)

- **`shop/`** – Shop-specific features:
  - Product catalog management
  - Cart and wishlist functionality
  - Order processing and fulfillment
  - Vendor dashboard

- **`authentications/`** – User management:
  - Registration, login, password management
  - Role-based access control (customer vs. vendor)
  - Session handling

### 2. **Templates**
- **Base templates** (`templates/`) – Shared layout, navigation, breadcrumbs
- **Page templates** (`pages/`) – Dynamic content rendered per request
- **App templates** (`sumia/templates/`) – Context-specific rendering

### 3. **Configuration & Deployment**
- `deployment.yaml` – Production deployment settings
- `requirements.txt` – Python dependencies (Django, django-taggit, jazzmin, etc.)
- `manage.py` – Standard Django CLI entry point
- `.gitignore` – Excludes build artifacts, cache, and secret files

### 4. **Documentation**
- `docs/scope.md` – Project scope and feature list
- `docs/project_structure.md` – This file
- `STYLING_GUIDE.md` – UI/UX design guidelines

## Technology Stack

| Layer | Technology |
|-------|------------|
| Framework | Django 4.2+ |
| Frontend | HTML5, CSS3, Bootstrap 5, Select2 |
| Tagging | django-taggit + Select2.js |
| Admin | Django admin with Jazzmin theme |
| Static Files | Pillow (image processing) |
| Deployment | ASGI (Daphne/uvicorn) |

## Development Flow

1. **Clone** → `git clone <repo>`
2. **Virtual Environment** → `python -m venv venv`
3. **Install Dependencies** → `pip install -r requirements.txt`
4. **Apply Migrations** → `python manage.py migrate`
5. **Create Superuser** → `python manage.py createsuperuser`
6. **Run Server** → `python manage.py runserver`

---
