"""Access control for the role dashboards."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pages.models import Cart, CartItem, Order, OrderItem, Product, Wishlist

User = get_user_model()


class DashboardAccessTests(TestCase):
    """The two dashboards are mutually exclusive.

    `login_user` routes each account to its own dashboard, so a customer
    landing on the vendor one (or the other way round) is a permission
    failure, not a navigation mistake worth bouncing.
    """

    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer', password='pass12345', account_type='user'
        )
        self.vendor = User.objects.create_user(
            username='vendor', password='pass12345', account_type='vendor'
        )

    def login(self, user):
        self.assertTrue(
            self.client.login(username=user.username, password='pass12345')
        )

    def test_vendor_can_open_the_vendor_dashboard(self):
        self.login(self.vendor)
        self.assertEqual(
            self.client.get(reverse('vendor_dashboard')).status_code, 200
        )

    def test_customer_can_open_the_user_dashboard(self):
        self.login(self.customer)
        self.assertEqual(
            self.client.get(reverse('user_dashboard')).status_code, 200
        )

    def test_customer_cannot_access_vendor_dashboard(self):
        self.login(self.customer)
        response = self.client.get(reverse('vendor_dashboard'))

        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, 'My Products', status_code=403)

    def test_vendor_cannot_access_user_dashboard(self):
        self.login(self.vendor)
        response = self.client.get(reverse('user_dashboard'))

        self.assertEqual(response.status_code, 403)

    def test_anonymous_visitor_is_sent_to_login(self):
        for name in ('vendor_dashboard', 'user_dashboard'):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))

                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.url, f'{reverse("login")}?next={reverse(name)}'
                )


class VendorDashboardFigureTests(TestCase):
    """The vendor dashboard counts only the signed in vendor's own rows."""

    def setUp(self):
        self.vendor = User.objects.create_user(
            username='vendor', password='pass12345', account_type='vendor'
        )
        self.customer = User.objects.create_user(
            username='customer', password='pass12345', account_type='user'
        )
        self.rival = User.objects.create_user(
            username='rival', password='pass12345', account_type='vendor'
        )

        self.live = Product.objects.create(
            name='Live Item', description='On sale', price=1000,
            stock_quantity=40, creator=self.vendor,
        )
        self.running_low = Product.objects.create(
            name='Nearly Gone', description='Low', price=500,
            stock_quantity=2, creator=self.vendor,
        )
        self.rivals_product = Product.objects.create(
            name='Rival Item', description='Theirs', price=7000,
            stock_quantity=90, creator=self.rival,
        )

        self.mine = Order.objects.create(user=self.customer, total_price=3000)
        OrderItem.objects.create(
            order=self.mine, product=self.live, quantity=2, price_at_purchase=1000
        )
        OrderItem.objects.create(
            order=self.mine, product=self.running_low, quantity=1, price_at_purchase=500
        )
        OrderItem.objects.create(
            order=self.mine, product=self.rivals_product, quantity=1,
            price_at_purchase=7000,
        )
        self.theirs = Order.objects.create(user=self.customer, total_price=7000)
        OrderItem.objects.create(
            order=self.theirs, product=self.rivals_product, quantity=1,
            price_at_purchase=7000,
        )
        self.cancelled = Order.objects.create(
            user=self.customer, total_price=1000, status='cancelled'
        )
        OrderItem.objects.create(
            order=self.cancelled, product=self.live, quantity=1, price_at_purchase=1000
        )

    def login(self):
        self.assertTrue(
            self.client.login(username=self.vendor.username, password='pass12345')
        )

    def stats(self):
        self.login()
        return self.client.get(reverse('vendor_dashboard')).context

    def test_figures_count_only_the_signed_in_vendors_own_rows(self):
        context = self.stats()

        self.assertEqual(context['product_count'], 2)
        self.assertEqual(context['live_product_count'], 2)
        self.assertEqual(context['low_stock_count'], 1)
        self.assertEqual(context['units_sold'], 3)
        self.assertEqual(context['revenue'], 2500)

    def test_revenue_and_units_exclude_cancelled_orders(self):
        """A cancelled line is still listed, but must not inflate the figures."""
        context = self.stats()

        self.assertEqual(context['units_sold'], 3)
        self.assertEqual(context['revenue'], 2500)
        self.assertIn(
            self.cancelled.order_number,
            [order.order_number for order in context['recent_orders']],
        )

    def test_dashboard_does_not_leak_the_rivals_orders(self):
        self.login()
        response = self.client.get(reverse('vendor_dashboard'))
        order_numbers = [order.order_number for order in response.context['recent_orders']]

        self.assertNotIn(self.theirs.order_number, order_numbers)
        self.assertNotContains(response, 'Rival Item')

    def test_recent_products_are_the_vendors_own(self):
        context = self.stats()

        self.assertEqual(
            {product.name for product in context['recent_products']},
            {'Live Item', 'Nearly Gone'},
        )


class CustomerDashboardFigureTests(TestCase):
    """The shopper dashboard counts only the signed in shopper's own rows."""

    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer', password='pass12345', account_type='user'
        )
        self.rival_customer = User.objects.create_user(
            username='rival-shopper', password='pass12345', account_type='user'
        )
        product = Product.objects.create(
            name='Desk Lamp', description='Bright', price=2500,
            stock_quantity=10, creator=self.customer,
        )
        self.order = Order.objects.create(user=self.customer, total_price=2500)
        OrderItem.objects.create(
            order=self.order, product=product, quantity=1, price_at_purchase=2500
        )
        Order.objects.create(user=self.rival_customer, total_price=99000)
        Wishlist.objects.create(user=self.customer, product=product)
        CartItem.objects.create(
            cart=Cart.objects.create(user=self.customer),
            product=product,
            quantity=2,
        )

    def test_figures_ignore_another_shoppers_activity(self):
        self.assertTrue(
            self.client.login(username=self.customer.username, password='pass12345')
        )
        response = self.client.get(reverse('user_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['order_count'], 1)
        self.assertEqual(response.context['total_spent'], 2500)
        self.assertEqual(response.context['cart_count'], 1)
        self.assertEqual(response.context['wishlist_count'], 1)
        self.assertEqual(
            [order.order_number for order in response.context['recent_orders']],
            [self.order.order_number],
        )

    def test_figures_are_zero_for_a_new_account(self):
        fresh = User.objects.create_user(
            username='fresh', password='pass12345', account_type='user'
        )
        self.assertTrue(
            self.client.login(username=fresh.username, password='pass12345')
        )
        response = self.client.get(reverse('user_dashboard'))

        self.assertEqual(response.context['order_count'], 0)
        self.assertEqual(response.context['total_spent'], 0)
        self.assertEqual(response.context['cart_count'], 0)
        self.assertEqual(response.context['wishlist_count'], 0)
