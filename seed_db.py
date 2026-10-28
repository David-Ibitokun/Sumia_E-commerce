"""Database Seeding Script for Sumia E-Commerce Deployment.

Usage:
    python seed_db.py

What this script does:
1. Creates an initial superuser/admin account if not already present.
2. Creates default demo accounts (a verified vendor and a customer).
3. Populates the comprehensive category tree (top-level + subcategories).
4. Creates popular brands.
5. Populates curated starter products with descriptions, pricing, discounts, and inventory.
6. Seeds initial product reviews and ratings.

Safe for repeated runs (idempotent: uses get_or_create and update_or_create).
"""
import os
import sys
import django

# Configure Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sumia.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from pages.models import Category, Brand, Product, ProductReview

User = get_user_model()

# 1x1 transparent PNG for mock product images if none exist
DUMMY_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08'
    b'\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00'
    b'\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


def seed_users():
    print("--> Seeding users...")
    # Admin Superuser
    admin_user = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@sumia.com')
    admin_pass = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin12345')

    if not User.objects.filter(username=admin_user).exists():
        User.objects.create_superuser(
            username=admin_user,
            email=admin_email,
            password=admin_pass,
            account_type='vendor'
        )
        print(f"  [+] Superuser '{admin_user}' created.")
    else:
        print(f"  [*] Superuser '{admin_user}' already exists.")

    # Demo Vendor
    vendor, created = User.objects.get_or_create(
        username='demovendor',
        defaults={
            'email': 'vendor@sumia.com',
            'account_type': 'vendor',
            'first_name': 'Sumia',
            'last_name': 'Merchant',
            'agreed_to_terms': True
        }
    )
    if created:
        vendor.set_password('vendor12345')
        vendor.save()
        print("  [+] Demo vendor 'demovendor' created.")
    else:
        print("  [*] Demo vendor 'demovendor' exists.")

    # Demo Customer
    customer, created = User.objects.get_or_create(
        username='democustomer',
        defaults={
            'email': 'customer@sumia.com',
            'account_type': 'user',
            'first_name': 'Jane',
            'last_name': 'Shopper',
            'agreed_to_terms': True
        }
    )
    if created:
        customer.set_password('customer12345')
        customer.save()
        print("  [+] Demo customer 'democustomer' created.")
    else:
        print("  [*] Demo customer 'democustomer' exists.")

    return vendor, customer


def seed_categories():
    print("--> Seeding categories...")
    category_tree = {
        'Phones & Tablets': [
            'Smartphones', 'Tablets', 'Mobile Accessories', 'Smartwatches',
            'Headphones & Earbuds', 'Chargers & Cables', 'Power Banks'
        ],
        'Electronics': [
            'Televisions', 'Home Audio', 'Cameras', 'Video Game Consoles',
            'Inverters', 'Fans', 'Air Conditioners'
        ],
        'Computing': [
            'Laptops', 'Desktops', 'Monitors', 'Computer Accessories',
            'Printers & Scanners', 'Storage Devices'
        ],
        'Fashion': [
            'Men\'s Clothing', 'Women\'s Clothing', 'Men\'s Shoes', 'Women\'s Shoes',
            'Watches', 'Jewelry', 'Bags & Luggage'
        ],
        'Health & Beauty': [
            'Fragrances', 'Skincare', 'Hair Care', 'Makeup',
            'Blood Pressure Monitors', 'Vitamins & Supplements'
        ],
        'Home & Kitchen': [
            'Kitchen Appliances', 'Furniture', 'Cookware', 'Bedding',
            'Home Decor', 'Lighting'
        ]
    }

    category_objects = {}
    for parent_name, subcats in category_tree.items():
        parent, _ = Category.objects.get_or_create(name=parent_name)
        category_objects[parent_name] = parent
        for sub_name in subcats:
            sub, _ = Category.objects.update_or_create(
                name=sub_name,
                defaults={'parent': parent}
            )
            category_objects[sub_name] = sub

    print(f"  [+] Synced category tree ({len(category_objects)} categories).")
    return category_objects


def seed_brands():
    print("--> Seeding brands...")
    brand_names = [
        'Apple', 'Samsung', 'Sony', 'Dell', 'HP', 'Lenovo',
        'Nike', 'Adidas', 'Panasonic', 'Omron', 'Xiaomi', 'LG'
    ]
    brands = {}
    for name in brand_names:
        b, _ = Brand.objects.get_or_create(name=name)
        brands[name] = b
    print(f"  [+] Synced {len(brands)} brands.")
    return brands


def seed_products(vendor, categories, brands):
    print("--> Seeding curated products...")
    product_specs = [
        {
            'name': 'Apple iPhone 15 Pro 256GB - Titanium',
            'category': 'Smartphones',
            'brand': 'Apple',
            'price': 1350000.00,
            'discount_price': 1280000.00,
            'stock_quantity': 15,
            'description': 'Experience the forged titanium design, A17 Pro chip, customizable Action button, and versatile 48MP camera system.',
            'tags': ['apple', 'iphone', 'flagship', 'smartphone'],
        },
        {
            'name': 'Samsung Galaxy S24 Ultra 512GB - Titanium Gray',
            'category': 'Smartphones',
            'brand': 'Samsung',
            'price': 1450000.00,
            'discount_price': 1380000.00,
            'stock_quantity': 12,
            'description': 'Galaxy AI is here. Search like never before, get real-time voice translation, and shoot in 200MP perfection with built-in S-Pen.',
            'tags': ['samsung', 'galaxy', 'ai', 'android'],
        },
        {
            'name': 'Sony WH-1000XM5 Wireless Noise Cancelling Headphones',
            'category': 'Headphones & Earbuds',
            'brand': 'Sony',
            'price': 420000.00,
            'discount_price': 385000.00,
            'stock_quantity': 25,
            'description': 'Industry-leading noise cancellation with two processors and eight microphones for unprecedented sound purity and 30-hour battery life.',
            'tags': ['sony', 'audio', 'anc', 'headphones'],
        },
        {
            'name': 'Apple MacBook Pro 14" M3 Chip 512GB SSD',
            'category': 'Laptops',
            'brand': 'Apple',
            'price': 2100000.00,
            'discount_price': 1950000.00,
            'stock_quantity': 8,
            'description': 'The most advanced chips ever built for a personal computer. Up to 22 hours of battery life and Liquid Retina XDR display.',
            'tags': ['macbook', 'apple', 'laptop', 'pro'],
        },
        {
            'name': 'Dell XPS 15 9530 Core i9 32GB RAM 1TB SSD',
            'category': 'Laptops',
            'brand': 'Dell',
            'price': 2250000.00,
            'discount_price': None,
            'stock_quantity': 6,
            'description': 'Creator Edition powerhouse laptop featuring a 3.5K OLED touch display, NVIDIA GeForce RTX 4070 graphics, and precision aluminum chassis.',
            'tags': ['dell', 'laptop', 'xps', 'oled'],
        },
        {
            'name': 'Panasonic 3HP Inverter Standing Air Conditioner',
            'category': 'Air Conditioners',
            'brand': 'Panasonic',
            'price': 3100000.00,
            'discount_price': 2950000.00,
            'stock_quantity': 5,
            'description': 'Energy-saving floor standing air conditioner with Nanoe-X air purification technology and rapid cooling capability.',
            'tags': ['panasonic', 'cooling', 'inverter', 'appliances'],
        },
        {
            'name': 'Omron BF511 Full Body Composition Monitor',
            'category': 'Blood Pressure Monitors',
            'brand': 'Omron',
            'price': 350000.00,
            'discount_price': 320000.00,
            'stock_quantity': 20,
            'description': 'Clinically validated family body composition monitor measuring visceral fat, skeletal muscle, body fat percentage, and resting metabolism.',
            'tags': ['health', 'fitness', 'omron', 'monitor'],
        },
        {
            'name': 'Nike Air Zoom Pegasus 40 Running Shoes',
            'category': "Men's Shoes",
            'brand': 'Nike',
            'price': 125000.00,
            'discount_price': 98000.00,
            'stock_quantity': 30,
            'description': 'A springy ride for any run with responsive React foam and dual Zoom Air units for a smooth transition from heel to toe.',
            'tags': ['nike', 'shoes', 'running', 'sport'],
        },
        {
            'name': 'Sony PlayStation 5 Slim Console Edition',
            'category': 'Video Game Consoles',
            'brand': 'Sony',
            'price': 720000.00,
            'discount_price': 685000.00,
            'stock_quantity': 14,
            'description': 'Experience lightning-fast loading with an ultra-high speed 1TB SSD, deeper immersion with haptic feedback, and all-new slim design.',
            'tags': ['gaming', 'playstation', 'ps5', 'console'],
        },
        {
            'name': 'LG C3 65-Inch 4K OLED evo Smart TV',
            'category': 'Televisions',
            'brand': 'LG',
            'price': 2400000.00,
            'discount_price': 2190000.00,
            'stock_quantity': 7,
            'description': 'Self-lit OLED pixels shine brighter with Brightness Booster. Ultimate gaming experience with 0.1ms response time and Dolby Vision IQ.',
            'tags': ['tv', 'oled', 'lg', '4k'],
        }
    ]

    created_products = []
    for spec in product_specs:
        cat = categories.get(spec['category'])
        brand = brands.get(spec['brand'])

        product, created = Product.objects.get_or_create(
            name=spec['name'],
            defaults={
                'description': spec['description'],
                'price': spec['price'],
                'discount_price': spec['discount_price'],
                'stock_quantity': spec['stock_quantity'],
                'category': cat,
                'brand': brand,
                'creator': vendor,
                'is_available': True,
                'image': SimpleUploadedFile('product_seed.png', DUMMY_PNG, content_type='image/png')
            }
        )
        if created and spec.get('tags'):
            product.tags.add(*spec['tags'])
            print(f"  [+] Created product: {product.name}")
        else:
            print(f"  [*] Product exists: {product.name}")

        created_products.append(product)

    return created_products


def seed_reviews(customer, products):
    print("--> Seeding customer reviews...")
    sample_reviews = [
        ("Absolute game changer!", "Build quality and performance exceeded my expectations. Delivery was prompt.", 5),
        ("Great value for money", "Very satisfied with this purchase. Everything works as advertised.", 4),
        ("Excellent product", "Fast nationwide delivery, packaged securely, and top-tier build.", 5),
    ]

    count = 0
    for i, prod in enumerate(products[:3]):
        title, comment, rating = sample_reviews[i % len(sample_reviews)]
        review, created = ProductReview.objects.get_or_create(
            product=prod,
            user=customer,
            defaults={
                'title': title,
                'comment': comment,
                'rating': rating,
                'is_verified_purchase': True,
                'is_approved': True
            }
        )
        if created:
            count += 1

    print(f"  [+] Seeded {count} customer reviews.")


def main():
    print("==================================================")
    print("   Sumia Marketplace Database Seeding Initializer   ")
    print("==================================================")
    vendor, customer = seed_users()
    categories = seed_categories()
    brands = seed_brands()
    products = seed_products(vendor, categories, brands)
    seed_reviews(customer, products)
    print("==================================================")
    print(" [OK] Database seeding completed successfully!")
    print("==================================================")


if __name__ == '__main__':
    main()
