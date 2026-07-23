import datetime

from django.test import TestCase

from users.models import TelegramUser
from .models import Product


class ProductModelTest(TestCase):
    def setUp(self):
        self.seller = TelegramUser.objects.create_user(username='seller', telegram_id=1)
        self.buyer = TelegramUser.objects.create_user(username='buyer', telegram_id=2)

    def test_create_unsold_product(self):
        product = Product.objects.create(
            product_name='iPhone 15',
            income_price='900.00',
            imei_code='123456789012345',
            seller=self.seller,
            purchase_date=datetime.date(2024, 1, 10),
        )
        self.assertFalse(product.is_sold)
        self.assertIsNone(product.sold_date)
        self.assertEqual(str(product), 'iPhone 15')

    def test_create_sold_product(self):
        product = Product.objects.create(
            product_name='Samsung S24',
            income_price='800.00',
            imei_code='987654321098765',
            seller=self.seller,
            buyer=self.buyer,
            purchase_date=datetime.date(2024, 1, 10),
            sold_date=datetime.date(2024, 2, 15),
            is_sold=True,
        )
        self.assertTrue(product.is_sold)
        self.assertEqual(product.buyer, self.buyer)
