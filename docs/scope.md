# Project Scope

## Overview

Sumia is a modern, responsive Django-based e-commerce web application designed for seamless product browsing, vendor management, category navigation, tag suggestion, and secure checkout.

## Scope Definition

### In-Scope Features

The Sumia platform includes the following core capabilities:

#### 1. User Authentication & Authorization
- User registration with terms agreement
- Login/logout functionality
- Password change flows
- Custom user model (`UsersRegistration`) with user/vendor account types
- Session-based authentication

#### 2. Product Catalog Management
- Hierarchical categories with parent/child relationships
- Brand management
- Product creation, editing, and deletion
- Product images with automatic slug generation
- Price and discount pricing support
- Stock quantity tracking
- Product availability flags

#### 3. Tag System
- Integration with `django-taggit`
- Tag autocomplete with Select2
- Tag-based product filtering and suggestions

#### 4. Vendor Dashboard
- Vendor product management (add/edit/delete)
- Vendor order tracking and management
- Order status updates (pending, processing, shipped, delivered, cancelled)

#### 5. Shopping Cart & Wishlist
- Add/remove products from cart
- Quantity updates
- Cart total calculations
- Wishlist with unique constraint per user per product

#### 6. Order Management
- Order creation with unique order numbers (date-based + UUID)
- Multiple payment methods (COD, Card, Bank Transfer)
- Order status tracking
- Shipping information collection
- Guest order support via session keys
- Order history for users

#### 7. Search & Filtering
- Product search by name
- Category-based browsing
- Brand-based filtering
- Tag-based filtering

#### 8. Navigation & UX
- Breadcrumb navigation
- Hierarchical category sidebar with hover subcategories
- SVG icon support for categories (Font Awesome)
- Responsive design (Bootstrap 5)

#### 9. Admin Interface
- Django admin with Jazzmin theme
- Custom admin styling

#### 10. Additional Features
- Image preview before upload
- Email notifications (framework in place)
- Category icon auto-assignment based on name matching
- Static file serving with WhiteNoise

### Out-of-Scope Features

The following are explicitly NOT part of this project's scope:

- Payment gateway integration (no Stripe/PayPal processing)
- Real-time chat support
- Multi-currency support
- Advanced analytics dashboard
- Mobile native applications
- Recommendation engine
- Subscription-based features
- Marketplace seller onboarding workflow beyond basic vendor registration

### Target Users

1. **Customers (Buyers)**
   - Browse products by category, brand, and tags
   - Add items to cart and wishlist
   - Place orders
   - View order history

2. **Vendors**
   - Manage product listings
   - View and update order statuses
   - Access vendor dashboard

3. **Administrators**
   - Manage categories, brands, and products
   - View all orders and users
   - Configure site settings

### Assumptions & Constraints

- Django 4.2+ framework
- SQLite for local development; PostgreSQL/MySQL supported via configuration
- Bootstrap 5 for frontend responsiveness
- Session-based cart persistence
- Single-region deployment (no multi-region considerations)
