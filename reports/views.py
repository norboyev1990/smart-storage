from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser

from products.models import Product
from .serializers import ProductReportSerializer


class RemainingItemsView(ListAPIView):
    """Report: products that have NOT been sold yet."""
    serializer_class = ProductReportSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_sold=False)
            .select_related('buyer', 'seller')
            .order_by('purchase_date')
        )


class SoldItemsView(ListAPIView):
    """Report: products that have been sold."""
    serializer_class = ProductReportSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_sold=True)
            .select_related('buyer', 'seller')
            .order_by('sold_date')
        )
