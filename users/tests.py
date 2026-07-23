from django.test import TestCase

from .models import TelegramUser


class TelegramUserModelTest(TestCase):
    def test_create_user(self):
        user = TelegramUser.objects.create_user(
            username='testuser',
            first_name='John',
            last_name='Doe',
            telegram_id=123456789,
            phone_number='+998901234567',
        )
        self.assertEqual(str(user), 'John Doe')
        self.assertEqual(user.telegram_id, 123456789)
        self.assertEqual(user.phone_number, '+998901234567')

    def test_user_str_fallback_to_username(self):
        user = TelegramUser.objects.create_user(username='noname')
        self.assertEqual(str(user), 'noname')
