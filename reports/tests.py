import datetime

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from products.models import Product
from users.models import TelegramUser


class ReportViewTest(TestCase):
    def setUp(self):
        self.admin = TelegramUser.objects.create_superuser(
            username='admin', password='password'
        )
        self.seller = TelegramUser.objects.create_user(username='seller', telegram_id=10)
        self.buyer = TelegramUser.objects.create_user(username='buyer', telegram_id=20)

        Product.objects.create(
            product_name='Remaining Phone',
            income_price='500.00',
            seller=self.seller,
            purchase_date=datetime.date(2024, 1, 1),
            is_sold=False,
        )
        Product.objects.create(
            product_name='Sold Phone',
            income_price='600.00',
            seller=self.seller,
            buyer=self.buyer,
            purchase_date=datetime.date(2024, 1, 5),
            sold_date=datetime.date(2024, 2, 1),
            is_sold=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_remaining_items_report(self):
        url = reverse('report-remaining')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['product_name'], 'Remaining Phone')

    def test_sold_items_report(self):
        url = reverse('report-sold')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['product_name'], 'Sold Phone')
