from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('buyer', 'seller').order_by('id')
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]
