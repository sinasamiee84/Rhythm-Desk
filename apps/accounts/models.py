from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    phone_number = models.CharField(
        max_length=15,
        verbose_name="شماره تماس",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="کاربر"
    )
    avatar = models.ImageField(
        upload_to='doctors_avatars/',
        blank=True,
        null=True,
        verbose_name="تصویر پروفایل"
    )
    medical_license_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="شماره نظام پزشکی"
    )
    specialty = models.CharField(
        max_length=100,
        blank=True,
        default="متخصص قلب و عروق / مهندسی پزشکی",
        verbose_name="تخصص"
    )
    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name="درباره پزشک"
    )

    class Meta:
        verbose_name = "پروفایل پزشک"
        verbose_name_plural = "پروفایل‌های پزشکان"

    def __str__(self):
        return f"پروفایل دکتر {self.user.get_full_name() or self.user.username}"


# سیگنال برای ساخت یا به‌روزرسانی خودکار پروفایل
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # اگر کاربر وجود داشت، مطمئن شویم پروفایل دارد
        Profile.objects.get_or_create(user=instance)
