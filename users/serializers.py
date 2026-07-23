from rest_framework import serializers

from .models import TelegramUser


class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = ('id', 'username', 'first_name', 'last_name', 'telegram_id', 'phone_number')
