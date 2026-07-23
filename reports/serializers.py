from rest_framework import serializers

from products.models import Product
from users.serializers import TelegramUserSerializer


class ProductReportSerializer(serializers.ModelSerializer):
    buyer = TelegramUserSerializer(read_only=True)
    seller = TelegramUserSerializer(read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'product_name', 'income_price', 'imei_code', 'photo',
            'buyer', 'seller', 'purchase_date', 'sold_date', 'is_sold',
        )
