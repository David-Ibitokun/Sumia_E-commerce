# pages/management/commands/populate_categories.py

from django.core.management.base import BaseCommand
from pages.models import Category  # Ensure this matches your actual app name

class Command(BaseCommand):
    help = 'Populates the database with initial top-level and sub-level categories.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting category population/update process...'))

        main_categories_data = self.get_main_categories_data()
        created_main_categories = {}
        total_new_categories = 0

        # --- Create Main Categories (Top-Level) ---
        self.stdout.write(self.style.HTTP_INFO('Processing main categories...'))
        for cat_name in main_categories_data:
            category, created = Category.objects.get_or_create(name=cat_name, parent=None)
            created_main_categories[cat_name] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created main category: {cat_name}'))
                total_new_categories += 1

        # --- Helper function to add subcategories ---
        def add_subcategories(parent_name, subcat_list):
            nonlocal total_new_categories
            parent = created_main_categories.get(parent_name)
            if not parent:
                self.stdout.write(self.style.ERROR(f'Main category "{parent_name}" not found. Cannot add subcategories.'))
                return

            for subcat_name in subcat_list:
                _, created = Category.objects.get_or_create(name=subcat_name, parent=parent)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Created subcategory: {subcat_name} under {parent_name}'))
                    total_new_categories += 1

        self.stdout.write(self.style.HTTP_INFO('Processing subcategories...'))

        # --- Define and Add Subcategories for each Main Category ---
        subcategory_map = {
            'Phones & Tablets': [
                'Smartphones', 'Tablets', 'Mobile Accessories', 'Feature Phones', 'Smartwatches',
                'Phone Cases & Covers', 'Screen Protectors', 'Chargers & Cables', 'Power Banks',
                'Headphones & Earbuds', 'Bluetooth Speakers', 'Car Phone Holders',
                'Other Phones & Tablets' # Added 'Other'
            ],
            'Electronics': [
                'Televisions', 'Home Audio', 'Cameras', 'Video Game Consoles', 'Drones', 'Fans',
                'Wearable Technology', 'Generators & Power Solutions', 'Security Cameras & Systems',
                'DVD & Blu-Ray Players', 'Projectors', 'Home Theatre Systems', 'Digital Cameras',
                'DSLR Cameras', 'Mirrorless Cameras', 'Action Cameras', 'Camera Accessories',
                'Gaming Accessories', 'Surge Protectors & Adapters', 'Smart Home Devices',
                'Other Electronics' # Added 'Other'
            ],
            'Computing': [
                'Laptops', 'Desktops', 'Printers & Scanners', 'Monitors', 'Computer Accessories',
                'Networking Products', 'Data Storage', 'Software', 'Gaming Laptops', 'Workstation PCs',
                'Ink & Toner', 'Keyboards', 'Mice', 'Webcams', 'External Hard Drives', 'SSDs',
                'USB Flash Drives', 'Routers', 'Modems', 'Antivirus Software', 'Office Suites',
                'Other Computing' # Added 'Other'
            ],
            'Fashion': [
                'Men\'s Fashion', 'Women\'s Fashion', 'Children\'s Fashion',
                'Watches', 'Jewellery', 'Bags', 'Shoes', 'Eyewear', 'Accessories', 'Men\'s Clothing',
                'Women\'s Clothing', 'Boy\'s Clothing', 'Girl\'s Clothing', 'Sandals', 'Sneakers',
                'Heels', 'Flats', 'Wallets', 'Belts', 'Hats', 'Scarves', 'Rings', 'Necklaces',
                'Earrings', 'Bracelets',
                'Other Fashion' # Added 'Other'
            ],
            'Beauty & Health': [
                'Fragrances', 'Skincare', 'Hair Care', 'Makeup', 'Personal Care',
                'Vitamins & Supplements', 'Medical Supplies', 'Oral Care', 'Sexual Wellness',
                'Perfumes', 'Colognes', 'Moisturizers', 'Cleansers', 'Shampoos', 'Conditioners',
                'Lipsticks', 'Foundations', 'Body Lotions', 'Soaps & Shower Gels', 'Hair Dryers',
                'Hair Straighteners', 'Blood Pressure Monitors', 'Thermometers', 'Toothbrushes',
                'Toothpaste',
                'Other Beauty & Health' # Added 'Other'
            ],
            'Home & Kitchen': [
                'Cookware', 'Small Appliances', 'Large Appliances', 'Home Decor', 'Furniture',
                'Bedding & Bath', 'Lighting', 'Cleaning Supplies', 'Kitchen & Dining Tools',
                'Pots & Pans', 'Blenders', 'Toasters', 'Microwaves', 'Refrigerators', 'Washing Machines',
                'Vacuum Cleaners', 'Detergents', 'Towels', 'Sheets', 'Lamps', 'Chandeliers',
                'Dining Sets', 'Sofa Sets', 'Mugs', 'Plates', 'Cutlery',
                'Other Home & Kitchen' # Added 'Other'
            ],
            'Baby, Kids & Toys': [
                'Baby Gear', 'Baby Feeding', 'Diapers & Wipes', 'Children\'s Apparel',
                'Toys & Games', 'Nursery Furniture', 'School Supplies', 'Strollers', 'Car Seats',
                'High Chairs', 'Baby Bottles', 'Formula', 'Disposable Diapers', 'Cloth Diapers', 'Dolls',
                'Action Figures', 'Board Games', 'Puzzles', 'Cribs', 'School Backpacks', # Fixed 'Backpacks' name
                'Other Baby, Kids & Toys' # Added 'Other'
            ],
            'Sports & Fitness': [
                'Exercise & Fitness', 'Team Sports', 'Outdoor Recreation', 'Sportswear',
                'Cycling', 'Racket Sports', 'Boxing & Martial Arts', 'Yoga & Pilates', 'Weight Training',
                'Treadmills', 'Exercise Bikes', 'Basketball', 'Football', 'Soccer', 'Camping Gear',
                'Hiking Equipment', 'Running Shoes', 'Jerseys', 'Tennis Rackets', 'Badminton Sets',
                'Punching Bags', 'Gloves',
                'Other Sports & Fitness' # Added 'Other'
            ],
            'Automotive': [
                'Car Electronics', 'Car Accessories', 'Auto Parts', 'Motorcycles & Scooters',
                'Motorcycle Accessories', 'Oils & Fluids', 'Car Stereos', 'GPS Navigators',
                'Seat Covers', 'Floor Mats', 'Brake Pads', 'Spark Plugs', 'Car Batteries', # Fixed 'Batteries' name
                'Helmets', 'Motorcycle Jackets', 'Engine Oil', 'Brake Fluid',
                'Other Automotive' # Added 'Other'
            ],
            'Books & Media': [
                'Fiction Books', 'Non-Fiction Books', 'Textbooks', 'Magazines', 'Movies & TV Shows',
                'Music CDs & Vinyl', 'E-readers & Accessories', 'Fantasy', 'Science Fiction',
                'Romance', 'Biographies', 'Self-Help', 'Cookbooks', 'Children\'s Books', 'Action',
                'Comedy', 'Drama', 'Pop', 'Rock', 'Classical',
                'Other Books & Media' # Added 'Other'
            ],
            'Gaming': [
                'Consoles', 'Gamepads & Controllers', 'Video Games', 'Gaming Chairs',
                'Gaming Keyboards', 'VR Headsets', 'PC Gaming Components', 'In-Game Currency',
                'Other Gaming' # Added 'Other'
            ],
            'Groceries': [
                'Food Cupboard', 'Snacks', 'Breakfast Items', 'Beverages', 'Cooking Ingredients',
                'Canned & Dry Foods', 'Oils & Seasoning', 'Dairy Products', 'Frozen Foods',
                'Other Groceries' # Added 'Other'
            ],
            'Office & School Supplies': [
                'Stationery', 'Writing Tools', 'Notebooks', 'Filing & Storage',
                'Office Furniture', 'Desk Accessories', 'Whiteboards & Boards', 'Calculators',
                'Other Office & School Supplies' # Added 'Other'
            ],
            'Arts & Crafts': [
                'Drawing & Painting', 'Craft Supplies', 'Sewing', 'Knitting & Yarn',
                'Sculpting & Molding', 'Beading & Jewelry Making', 'Art Paper & Pads',
                'Other Arts & Crafts' # Added 'Other'
            ],
            'Travel & Luggage': [
                'Suitcases', 'Travel Bags', 'Travel Backpacks', # Fixed 'Backpacks' name
                'Passport Holders', 'Travel Accessories', 'Luggage Sets', 'Toiletry Bags',
                'Other Travel & Luggage' # Added 'Other'
            ],
            'Pet Supplies': [
                'Dog Food', 'Cat Food', 'Pet Toys', 'Pet Grooming', 'Litter & Trays',
                'Pet Carriers', 'Leashes & Collars', 'Aquarium Supplies',
                'Other Pet Supplies' # Added 'Other'
            ],
            'Industrial & Scientific': [
                'Test Instruments', 'Power Tools', 'Lab Equipment', 'Safety Supplies',
                'Hand Tools', 'Hardware & Fasteners', 'Measuring Tools',
                'Other Industrial & Scientific' # Added 'Other'
            ],
            'Renewable Energy & Solar': [
                'Solar Panels', 'Inverters', 'Solar Batteries', # Fixed 'Batteries' name
                'Solar Lighting', 'Charge Controllers', 'Off-grid Appliances', 'Wind Turbines',
                'Other Renewable Energy & Solar' # Added 'Other'
            ]
        }

        # Iterate and add all subcategories
        for main_cat_name, subcats in subcategory_map.items():
            add_subcategories(main_cat_name, subcats)

        # --- Summary ---
        if total_new_categories > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully added/updated {total_new_categories} categories.'))
        else:
            self.stdout.write(self.style.WARNING('No new categories were added, all specified categories already existed.'))

    def get_main_categories_data(self):
        return [
            'Phones & Tablets', 'Electronics', 'Computing', 'Fashion', 'Beauty & Health',
            'Home & Kitchen', 'Baby, Kids & Toys', 'Sports & Fitness', 'Automotive',
            'Books & Media', 'Gaming', 'Groceries', 'Office & School Supplies',
            'Arts & Crafts', 'Travel & Luggage', 'Pet Supplies', 'Industrial & Scientific',
            'Renewable Energy & Solar',
        ]