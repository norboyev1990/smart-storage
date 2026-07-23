from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'product_name', 'income_price', 'imei_code',
        'seller', 'buyer', 'purchase_date', 'sold_date', 'is_sold',
    )
    list_filter = ('is_sold', 'purchase_date', 'sold_date')
    search_fields = ('product_name', 'imei_code')
    autocomplete_fields = ('buyer', 'seller')
