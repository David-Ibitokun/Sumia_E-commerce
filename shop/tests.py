"""Smoke tests covering the refactored shop views and services."""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from pages.models import Brand, Category, Order, OrderItem, Product

from shop.services import cart as cart_service
from shop.services import categories as category_service
from shop.services.exceptions import (
    InvalidQuantityError,
    OutOfStockError,
    ProductUnavailableError,
)

User = get_user_model()

PNG_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08'
    b'\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00'
    b'\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


def image(name='product.png'):
    return SimpleUploadedFile(name, PNG_BYTES, content_type='image/png')


class ShopTestCase(TestCase):
    """Shared fixtures: a shopper, a vendor, a category tree and products."""

    @classmethod
    def setUpTestData(cls):
        cls.shopper = User.objects.create_user(
            username='shopper', password='pass12345', account_type='user'
        )
        cls.vendor = User.objects.create_user(
            username='vendor', password='pass12345', account_type='vendor'
        )

        cls.electronics = Category.objects.create(name='Electronics')
        cls.phones = Category.objects.create(name='Phones', parent=cls.electronics)
        cls.smartphones = Category.objects.create(name='Smartphones', parent=cls.phones)

        cls.phone = Product.objects.create(
            name='Test Phone',
            description='A phone',
            price=50000,
            stock_quantity=5,
            creator=cls.vendor,
            category=cls.phones,
            image=image('phone.png'),
        )
        cls.laptop = Product.objects.create(
            name='Test Laptop',
            description='A laptop',
            price=250000,
            stock_quantity=2,
            creator=cls.vendor,
            category=cls.electronics,
            image=image('laptop.png'),
        )
        cls.unavailable = Product.objects.create(
            name='Discontinued Item',
            description='Gone',
            price=1000,
            stock_quantity=0,
            is_available=False,
            creator=cls.vendor,
            image=image('gone.png'),
        )

    def login(self, user=None):
        self.assertTrue(
            self.client.login(
                username=(user or self.shopper).username, password='pass12345'
            )
        )


class CategoryServiceTests(ShopTestCase):
    def test_descendant_ids_include_whole_subtree(self):
        self.assertEqual(
            set(category_service.descendant_ids(self.electronics)),
            {
                self.electronics.pk,
                self.phones.pk,
                self.smartphones.pk,
            },
        )

    def test_breadcrumb_is_root_first(self):
        breadcrumb = category_service.breadcrumb_for(self.smartphones)
        self.assertEqual(
            [item.name for item in breadcrumb],
            ['Electronics', 'Phones', 'Smartphones'],
        )

    def test_category_page_lists_products_of_descendants(self):
        response = self.client.get(
            reverse('category_detail', args=[self.electronics.slug])
        )
        self.assertEqual(response.status_code, 200)
        names = {product.name for product in response.context['products']}
        self.assertEqual(names, {'Test Phone', 'Test Laptop'})


class PublicPageTests(ShopTestCase):
    def test_home_page_lists_available_products(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        names = {product.name for product in response.context['products']}
        self.assertEqual(names, {'Test Phone', 'Test Laptop'})

    def test_product_detail_uses_one_view_for_both_routes(self):
        canonical = self.client.get(reverse('product_detail', args=[self.phone.slug]))
        legacy = self.client.get(reverse('singleProduct', args=[self.phone.slug]))
        self.assertEqual(canonical.status_code, 200)
        self.assertEqual(legacy.status_code, 200)

    def test_absolute_url_points_at_canonical_route(self):
        self.assertEqual(self.phone.get_absolute_url(), f'/product/{self.phone.slug}/')

    def test_login_page_is_served_by_the_authentications_app(self):
        response = self.client.post(
            reverse('login'), {'username': 'shopper', 'password': 'pass12345'}
        )
        self.assertRedirects(response, reverse('user_dashboard'))

    def test_static_pages_render(self):
        for name in ('about', 'contact'):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_unknown_url_renders_the_404_page(self):
        response = self.client.get('/no-such-page/')
        self.assertEqual(response.status_code, 404)

    def test_my_account_requires_login(self):
        response = self.client.get(reverse('my_account'))
        self.assertRedirects(response, f'{reverse("login")}?next=/my-account/')


class TemplateSmokeTests(ShopTestCase):
    """Render every page that base.html links to, to catch broken url names."""

    def test_anonymous_pages_render(self):
        for name in ('login', 'register', 'shop', 'search'):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_customer_pages_render(self):
        self.login()
        for name in (
            'home', 'user_dashboard', 'my_profile', 'my_account',
            'cart', 'wishlist', 'order_list',
        ):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_vendor_pages_render(self):
        self.login(self.vendor)
        product = self.phone
        product.brand = Brand.objects.create(name='Sumia')
        product.save(update_fields=['brand'])
        order = Order.objects.create(user=self.shopper, total_price=50000)
        OrderItem.objects.create(
            order=order, product=product, quantity=1, price_at_purchase=50000
        )

        pages = [
            reverse('vendor_dashboard'),
            reverse('product_list'),
            reverse('add_product'),
            reverse('vendor_orders'),
            reverse('vendor_order_detail', args=[order.order_number]),
            reverse('edit_product', args=[product.slug]),
            reverse('delete_product', args=[product.slug]),
        ]
        for url in pages:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_edit_form_opens_the_panel_of_the_products_category(self):
        self.login(self.vendor)
        response = self.client.get(reverse('edit_product', args=[self.phone.slug]))

        self.assertEqual(
            response.context['selected_category_id'], self.phones.pk
        )
        self.assertEqual(
            response.context['selected_parent_id'], self.electronics.pk
        )
        self.assertContains(response, f'value="{self.phones.pk}"')
        self.assertRegex(
            response.content.decode(),
            rf'id="subcat-{self.phones.pk}"[^>]*checked',
        )

    def test_add_form_keeps_the_posted_category_after_a_validation_error(self):
        self.login(self.vendor)
        response = self.client.post(
            reverse('add_product'),
            {'name': '', 'price': 1000, 'stock_quantity': 1, 'category': self.phones.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_category_id'], self.phones.pk)
        self.assertEqual(
            response.context['selected_parent_id'], self.electronics.pk
        )


class BrandTests(ShopTestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name='Sumia')
        self.phone.brand = self.brand
        self.phone.save(update_fields=['brand'])

    def test_brand_list_shows_every_brand(self):
        response = self.client.get(reverse('brand_list'))
        self.assertEqual(
            [brand.name for brand in response.context['brands']], ['Sumia']
        )

    def test_brand_detail_by_slug_and_by_pk(self):
        by_slug = self.client.get(reverse('brand_detail', args=[self.brand.slug]))
        by_pk = self.client.get(reverse('brand_detail_by_id', args=[self.brand.pk]))

        self.assertEqual(
            [product.name for product in by_slug.context['products']], ['Test Phone']
        )
        self.assertEqual(
            [product.name for product in by_pk.context['products']], ['Test Phone']
        )


class CartTests(ShopTestCase):
    def test_add_item_creates_the_cart_once(self):
        cart_service.add_item(self.shopper, self.phone, 2)
        cart_service.add_item(self.shopper, self.phone, 1)

        cart = cart_service.get_cart(self.shopper)
        items = cart_service.get_cart_items(cart)
        self.assertEqual([item.quantity for item in items], [3])
        self.assertEqual(cart_service.total_price(self.shopper), 150000)

    def test_add_item_rejects_unavailable_product(self):
        with self.assertRaises(ProductUnavailableError):
            cart_service.add_item(self.shopper, self.unavailable, 1)

    def test_add_item_respects_stock(self):
        with self.assertRaises(OutOfStockError):
            cart_service.add_item(self.shopper, self.laptop, 3)

    def test_add_item_rejects_invalid_quantity(self):
        with self.assertRaises(InvalidQuantityError):
            cart_service.add_item(self.shopper, self.phone, 'many')

    def test_add_to_cart_view_redirects_back(self):
        self.login()
        response = self.client.post(
            reverse('add_to_cart', args=[self.phone.pk]), {'quantity': 2}
        )
        self.assertRedirects(response, reverse('cart'))
        self.assertEqual(cart_service.item_count(self.shopper), 1)

    def test_update_quantity_and_remove(self):
        self.login()
        cart_service.add_item(self.shopper, self.phone, 2)
        item = cart_service.get_cart_items(cart_service.get_cart(self.shopper))[0]

        cart_service.set_item_quantity(self.shopper, item.pk, 4)
        self.assertEqual(cart_service.total_price(self.shopper), 200000)

        self.client.post(reverse('remove_from_cart', args=[item.pk]))
        self.assertEqual(cart_service.item_count(self.shopper), 0)

    def test_ajax_cart_count_for_anonymous_visitor(self):
        response = self.client.get(reverse('ajax_cart_count'))
        self.assertEqual(response.json(), {'cart_count': 0})

    def test_ajax_add_to_cart_requires_login(self):
        response = self.client.post(
            reverse('ajax_add_to_cart', args=[self.phone.pk]), {'quantity': 1}
        )
        self.assertEqual(response.status_code, 401)

    def test_ajax_add_to_cart_returns_counters(self):
        self.login()
        response = self.client.post(
            reverse('ajax_add_to_cart', args=[self.phone.pk]), {'quantity': 2}
        )
        self.assertEqual(response.json()['cart_count'], 1)
        self.assertEqual(response.json()['cart_total'], '100000.00')


class CheckoutTests(ShopTestCase):
    shipping = {
        'address': '1 Test Street',
        'city': 'Lagos',
        'zip_code': '100001',
        'country': 'Nigeria',
        'phone_number': '+2348000000000',
        'payment_method': 'COD',
    }

    def test_checkout_requires_a_non_empty_cart(self):
        self.login()
        response = self.client.get(reverse('checkout'))
        self.assertRedirects(response, reverse('cart'))

    def test_invalid_checkout_post_redisplays_form_errors(self):
        self.login()
        cart_service.add_item(self.shopper, self.phone, 1)

        response = self.client.post(reverse('checkout'), {'city': 'Lagos'})

        self.assertEqual(response.status_code, 200)
        self.assertIn('address', response.context['form'].errors)
        self.assertEqual(Order.objects.count(), 0)

    def test_unavailable_payment_method_is_rejected(self):
        self.login()
        cart_service.add_item(self.shopper, self.phone, 1)

        response = self.client.post(
            reverse('checkout'), {**self.shipping, 'payment_method': 'Card'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('payment_method', response.context['form'].errors)
        self.assertEqual(Order.objects.count(), 0)

    def test_valid_checkout_creates_order_and_empties_cart(self):
        self.login()
        cart_service.add_item(self.shopper, self.phone, 2)

        response = self.client.post(reverse('checkout'), self.shipping)

        order = Order.objects.get()
        self.assertRedirects(
            response, reverse('order_detail', args=[order.order_number])
        )
        self.assertEqual(order.total_price, 100000)
        self.assertFalse(order.is_paid)
        self.assertEqual(order.orderitem_set.get().price_at_purchase, 50000)
        self.assertEqual(cart_service.item_count(self.shopper), 0)

        self.phone.refresh_from_db()
        self.assertEqual(self.phone.stock_quantity, 3)

    def test_checkout_rejects_order_beyond_available_stock(self):
        self.login()
        cart_service.add_item(self.shopper, self.laptop, 2)
        self.laptop.stock_quantity = 1
        self.laptop.save(update_fields=['stock_quantity'])

        response = self.client.post(reverse('checkout'), self.shipping)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(cart_service.item_count(self.shopper), 1)


class WishlistTests(ShopTestCase):
    def test_add_twice_keeps_one_entry(self):
        self.login()
        self.client.post(reverse('add_to_wishlist', args=[self.phone.pk]))
        self.client.post(reverse('add_to_wishlist', args=[self.phone.pk]))
        self.assertEqual(self.client.get(reverse('wishlist')).context[
            'wishlist_items'
        ].count(), 1)

    def test_ajax_add_reports_already_saved(self):
        self.login()
        url = reverse('ajax_add_to_wishlist', args=[self.phone.pk])
        self.assertEqual(self.client.post(url).json()['status'], 'success')
        self.assertEqual(self.client.post(url).json()['status'], 'info')


class SearchTests(ShopTestCase):
    def test_search_matches_description(self):
        response = self.client.get(reverse('search'), {'q': 'laptop'})
        self.assertEqual(
            [product.name for product in response.context['products']],
            ['Test Laptop'],
        )

    def test_search_can_be_narrowed_to_a_category_subtree(self):
        response = self.client.get(
            reverse('search'), {'q': 'Test', 'category': self.electronics.pk}
        )
        self.assertEqual(
            {product.name for product in response.context['products']},
            {'Test Phone', 'Test Laptop'},
        )

    def test_ajax_search_returns_suggestions(self):
        response = self.client.get(reverse('ajax_search'), {'q': 'phone'})
        self.assertEqual(
            response.json()['results'][0]['detail_url'],
            reverse('product_detail', args=[self.phone.slug]),
        )

    def test_ajax_search_ignores_single_character_queries(self):
        response = self.client.get(reverse('ajax_search'), {'q': 'p'})
        self.assertEqual(response.json()['results'], [])


class VendorTests(ShopTestCase):
    def test_vendor_only_sees_own_order_lines(self):
        other_vendor = User.objects.create_user(
            username='other', password='pass12345', account_type='vendor'
        )
        other_product = Product.objects.create(
            name='Other Product',
            description='Elsewhere',
            price=1000,
            stock_quantity=1,
            creator=other_vendor,
        )
        order = Order.objects.create(user=self.shopper, total_price=51000)
        OrderItem.objects.create(order=order, product=self.phone, quantity=1, price_at_purchase=50000)
        OrderItem.objects.create(order=order, product=other_product, quantity=1, price_at_purchase=1000)

        self.login(self.vendor)
        response = self.client.get(reverse('vendor_order_detail', args=[order.order_number]))

        self.assertEqual(
            [item.product.name for item in response.context['vendor_order_items']],
            ['Test Phone'],
        )
        self.assertEqual(response.context['vendor_total_price'], 50000)


class ProductManagementTests(ShopTestCase):
    def test_vendor_product_list_only_shows_own_products(self):
        other_vendor = User.objects.create_user(
            username='other', password='pass12345', account_type='vendor'
        )
        Product.objects.create(
            name='Other Product',
            description='Elsewhere',
            price=1000,
            stock_quantity=1,
            creator=other_vendor,
        )

        self.login(self.vendor)
        response = self.client.get(reverse('product_list'))

        self.assertEqual(
            {product.name for product in response.context['products']},
            {'Test Phone', 'Test Laptop', 'Discontinued Item'},
        )

    def test_add_product_uses_the_form_for_category_and_brand(self):
        self.login(self.vendor)
        response = self.client.post(
            reverse('add_product'),
            {
                'name': 'New Gadget',
                'description': 'A gadget',
                'price': '7500',
                'stock_quantity': '4',
                'is_available': 'on',
                'image': image('gadget.png'),
                'category': self.phones.pk,
                'brand_name': 'Sumia',
                'tags': 'gadgets,new',
            },
        )

        self.assertRedirects(response, reverse('product_list'))
        product = Product.objects.get(name='New Gadget')
        self.assertEqual(product.creator, self.vendor)
        self.assertEqual(product.category, self.phones)
        self.assertEqual(product.brand.name, 'Sumia')
        self.assertEqual(
            set(product.tags.names()), {'gadgets', 'new'}
        )

    def test_add_product_rejects_unknown_category(self):
        self.login(self.vendor)
        response = self.client.post(
            reverse('add_product'),
            {
                'name': 'Bad Gadget',
                'description': 'A gadget',
                'price': '7500',
                'stock_quantity': '4',
                'image': image('bad.png'),
                'category': '99999',
                'brand_name': 'Sumia',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('category', response.context['form'].errors)
        self.assertFalse(Product.objects.filter(name='Bad Gadget').exists())

    def test_vendor_cannot_edit_another_vendors_product(self):
        other_vendor = User.objects.create_user(
            username='other', password='pass12345', account_type='vendor'
        )
        foreign_product = Product.objects.create(
            name='Foreign Product',
            description='Not yours',
            price=1000,
            stock_quantity=1,
            creator=other_vendor,
        )

        self.login(self.vendor)
        response = self.client.get(
            reverse('edit_product', args=[foreign_product.slug])
        )

        self.assertEqual(response.status_code, 404)


class OrderTests(ShopTestCase):
    def test_customer_cannot_open_another_customers_order(self):
        order = Order.objects.create(user=self.shopper, total_price=1000)
        other = User.objects.create_user(
            username='other-shopper', password='pass12345', account_type='user'
        )

        self.login(other)
        response = self.client.get(
            reverse('order_detail', args=[order.order_number])
        )

        self.assertEqual(response.status_code, 404)

    def test_order_list_only_lists_own_orders(self):
        Order.objects.create(user=self.shopper, total_price=1000)
        other = User.objects.create_user(
            username='other-shopper', password='pass12345', account_type='user'
        )
        Order.objects.create(user=other, total_price=2000)

        self.login()
        response = self.client.get(reverse('order_list'))

        self.assertEqual(len(response.context['orders']), 1)


class VendorAccessControlTests(ShopTestCase):
    """Vendor pages need a vendor account, and only ever the vendor's own rows.

    `vendor_required` rejects a signed in customer with 403 and sends an
    anonymous visitor to the login page. Ownership is enforced separately, by
    filtering the query, so a valid vendor guessing an id still gets a 404.
    """

    def setUp(self):
        self.other_vendor = User.objects.create_user(
            username='other-vendor', password='pass12345', account_type='vendor'
        )
        self.foreign_product = Product.objects.create(
            name='Foreign Product',
            description='Belongs to another vendor',
            price=1000,
            stock_quantity=1,
            creator=self.other_vendor,
        )
        self.other_shopper = User.objects.create_user(
            username='other-shopper', password='pass12345', account_type='user'
        )
        # An order the signed in vendor has no line in, and an order of a
        # customer the signed in shopper does not own.
        self.unrelated_order = Order.objects.create(
            user=self.shopper, total_price=1000
        )
        OrderItem.objects.create(
            order=self.unrelated_order,
            product=self.foreign_product,
            quantity=1,
            price_at_purchase=1000,
        )
        self.other_customers_order = Order.objects.create(
            user=self.other_shopper, total_price=50000
        )
        OrderItem.objects.create(
            order=self.other_customers_order,
            product=self.phone,
            quantity=1,
            price_at_purchase=50000,
        )

    def vendor_urls(self):
        """Every vendor only URL, including the ones taking an argument."""
        return (
            reverse('vendor_dashboard'),
            reverse('product_list'),
            reverse('add_product'),
            reverse('vendor_orders'),
            reverse('vendor_order_detail', args=[self.unrelated_order.order_number]),
            reverse('edit_product', args=[self.foreign_product.slug]),
            reverse('delete_product', args=[self.foreign_product.slug]),
        )

    def test_customer_cannot_access_vendor_pages(self):
        self.login()
        for url in self.vendor_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_customer_cannot_open_the_vendor_dashboard(self):
        self.login()
        response = self.client.get(reverse('vendor_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_add_a_product(self):
        self.login()
        response = self.client.post(
            reverse('add_product'),
            {
                'name': 'Smuggled',
                'description': 'Not allowed',
                'price': '1000',
                'stock_quantity': '1',
                'image': image('smuggled.png'),
                'category': self.phones.pk,
                'brand_name': 'Sumia',
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Product.objects.filter(name='Smuggled').exists())

    def test_anonymous_users_are_redirected_to_login(self):
        for url in self.vendor_urls():
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.url, f'{reverse("login")}?next={url}'
                )

    def test_anonymous_users_cannot_reach_any_private_page(self):
        private_urls = [
            reverse('vendor_dashboard'),
            reverse('user_dashboard'),
            reverse('my_profile'),
            reverse('my_account'),
            reverse('product_list'),
            reverse('add_product'),
            reverse('vendor_orders'),
            reverse('order_list'),
            reverse('wishlist'),
            reverse('checkout'),
            reverse('order_detail', args=[self.other_customers_order.order_number]),
        ]

        for url in private_urls:
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.url, f'{reverse("login")}?next={url}'
                )

    def test_vendor_cannot_edit_another_vendors_product(self):
        self.login(self.vendor)

        response = self.client.get(
            reverse('edit_product', args=[self.foreign_product.slug])
        )
        self.assertEqual(response.status_code, 404)

        post = self.client.post(
            reverse('edit_product', args=[self.foreign_product.slug]),
            {
                'name': 'Hijacked',
                'description': 'Rewritten',
                'price': '1',
                'stock_quantity': '1',
            },
        )
        self.assertEqual(post.status_code, 404)

        self.foreign_product.refresh_from_db()
        self.assertEqual(self.foreign_product.name, 'Foreign Product')
        self.assertEqual(self.foreign_product.creator, self.other_vendor)

    def test_vendor_cannot_delete_another_vendors_product(self):
        self.login(self.vendor)
        url = reverse('delete_product', args=[self.foreign_product.slug])

        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(Product.objects.filter(pk=self.foreign_product.pk).exists())

    def test_vendor_cannot_access_unrelated_order_information(self):
        self.login(self.vendor)
        response = self.client.get(
            reverse('vendor_order_detail', args=[self.unrelated_order.order_number])
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, 'Foreign Product', status_code=404)

    def test_unrelated_orders_are_absent_from_the_vendor_order_list(self):
        self.login(self.vendor)
        response = self.client.get(reverse('vendor_orders'))

        order_numbers = [order.order_number for order in response.context['orders']]
        self.assertNotIn(self.unrelated_order.order_number, order_numbers)
        self.assertEqual(order_numbers, [self.other_customers_order.order_number])
        self.assertEqual(
            response.context['orders'].get().vendor_total_amount, 50000
        )

    def test_vendor_cannot_read_a_customers_order_through_the_vendor_route(self):
        """The order the vendor does sell into is still not a customer order."""
        self.login(self.vendor)
        response = self.client.get(
            reverse(
                'vendor_order_detail', args=[self.other_customers_order.order_number]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item.product.name for item in response.context['vendor_order_items']],
            ['Test Phone'],
        )
        self.assertEqual(response.context['vendor_total_price'], 50000)

    def test_user_cannot_view_another_users_order(self):
        self.login()
        response = self.client.get(
            reverse('order_detail', args=[self.other_customers_order.order_number])
        )

        self.assertEqual(response.status_code, 404)

    def test_customer_cannot_see_another_customers_orders_in_the_list(self):
        self.login()

        response = self.client.get(reverse('order_list'))

        self.assertEqual(
            [order.order_number for order in response.context['orders']],
            [self.unrelated_order.order_number],
        )


class NavigationCategoryCacheTests(ShopTestCase):
    def test_category_changes_invalidate_the_cached_tree(self):
        self.client.get(reverse('home'))

        Category.objects.create(name='Appliances')

        response = self.client.get(reverse('home'))
        names = {
            category.name for category in response.context['top_level_categories']
        }
        self.assertIn('Appliances', names)
