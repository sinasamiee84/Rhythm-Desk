from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import Profile

User = get_user_model()

class AccountsTests(TestCase):
    def setUp(self):
        self.username = "dr_alavi"
        self.password = "SecurePass123!"
        self.user = User.objects.create_user(
            username=self.username,
            email="alavi@cardioflow.ir",
            password=self.password,
            phone_number="09123456789"
        )

    def test_user_creation_and_profile_signal(self):
        """تست ایجاد کاربر و سیگنال ساخت خودکار پروفایل"""
        self.assertEqual(self.user.username, self.username)
        self.assertEqual(self.user.phone_number, "09123456789")
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)

    def test_login_view(self):
        """تست صفحه ورود و احراز هویت"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

        login_success = self.client.login(username=self.username, password=self.password)
        self.assertTrue(login_success)

        response = self.client.post(reverse('accounts:login'), {
            'username': self.username,
            'password': self.password
        })
        self.assertRedirects(response, reverse('patients:list'))

    def test_register_view(self):
        """تست صفحه ثبت‌نام"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_logout_view(self):
        """تست خروج از سیستم"""
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))
