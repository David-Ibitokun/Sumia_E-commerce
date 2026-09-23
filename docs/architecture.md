# Architecture & Technical Design

## Overview

Sumia follows a **Model-View-Template (MVT)** architecture consistent with Django conventions. The application is split into domain-specific apps (`sumia`, `shop`, `authentications`, `pages`) to keep concerns separated.

## High-Level Architecture

```
┌─────────────────────────────────────────────────┐
│                    Client (Browser)               │
├─────────────────────────────────────────────────┤
│              Bootstrap 5 + Select2                │
├─────────────────────────────────────────────────┤
│              Django URL Router                    │
│         sumia/urls.py → pages/urls.py            │
├─────────────────────────────────────────────────┤
│                   Views Layer                     │
│   sumia/views.py | shop/views.py | pages/views.py│
├─────────────────────────────────────────────────┤
│                  Forms Layer                      │
│          shop/forms.py | authentications/         │
├─────────────────────────────────────────────────┤
│                  Models Layer                     │
│  sumia/models.py | shop/models.py | pages/models │
├─────────────────────────────────────────────────┤
│                  Django ORM                       │
│            (SQLite / PostgreSQL / MySQL)          │
├─────────────────────────────────────────────────┤
│            django-taggit | Select2 | Jazzmin      │
└─────────────────────────────────────────────────┘
```

## App Responsibilities

| App | Purpose |
|-----|---------|
| **`sumia`** | Core domain models, shared views, base templates, site-wide configuration |
| **`shop`** | Product CRUD, cart, wishlist, order lifecycle, vendor dashboard |
| **`authentications`** | User registration/login, vendor onboarding, session management |
| **`pages`** | Static pages, custom admin, templatetags, context processors |

## Data Flow

1. **Request** → URL router maps to a view function
2. **View** → Processes form data / query params, calls model methods
3. **Model** → ORM queries or mutations on the database
4. **Template** → Renders HTML with context variables
5. **Response** → Rendered HTML returned to client

## Key Design Decisions

- **Session-based cart** – Cart persists via session keys (supports guest checkout)
- **Tag autocomplete** – `django-taggit` + `select2.js` for real-time tag suggestions
- **Hierarchical categories** – Self-referencing `Category` model with parent/child relationships
- **SVG icons** – Categories display icons via Font Awesome SVGs
- **Jazzmin admin** – Custom admin theme for better UX

## External Services

- **Email** – Framework in place; no provider configured yet
- **Payment** – Out of scope (no Stripe/PayPal integration)
- **Static files** – Served via WhiteNoise (static hosting)

## Security Considerations

- CSRF protection enabled (Django default)
- Password hashing via Django auth system
- Role-based access (customer vs vendor vs admin)
- `.gitignore` excludes `.env` and secret keys

---
