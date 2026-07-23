from django.conf import settings
from django.db import models


class Product(models.Model):
    product_name = models.CharField(max_length=255)
    income_price = models.DecimalField(max_digits=12, decimal_places=2)
    imei_code = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to='products/', blank=True, null=True)
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bought_products',
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sold_products',
    )
    purchase_date = models.DateField(null=True, blank=True)
    sold_date = models.DateField(null=True, blank=True)
    is_sold = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.product_name
