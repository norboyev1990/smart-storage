from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id', 'product_name', 'income_price', 'imei_code', 'photo',
            'buyer', 'seller', 'purchase_date', 'sold_date', 'is_sold',
        )
