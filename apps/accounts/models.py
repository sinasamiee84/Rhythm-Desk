from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # فیلد شماره تماس با محدودیت ۱۵ کاراکتر (مناسب برای فرمت‌های بین‌المللی)
    phone_number = models.CharField(
        max_length=15,
        verbose_name="شماره تماس",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.username
