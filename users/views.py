from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .models import TelegramUser
from .serializers import TelegramUserSerializer


class TelegramUserViewSet(viewsets.ModelViewSet):
    queryset = TelegramUser.objects.all().order_by('id')
    serializer_class = TelegramUserSerializer
    permission_classes = [IsAdminUser]
