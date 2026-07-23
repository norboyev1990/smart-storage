from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'telegram_id', 'phone_number', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Telegram Info', {'fields': ('telegram_id', 'phone_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Telegram Info', {'fields': ('telegram_id', 'phone_number')}),
    )
