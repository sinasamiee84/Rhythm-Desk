from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin, StackedInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from .models import Profile

User = get_user_model()

class ProfileInline(StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "اطلاعات پروفایل پزشک"
    fk_name = 'user'


# لغو ثبت قبلی برای جلوگیری از خطای AlreadyRegistered
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(ModelAdmin, BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    inlines = [ProfileInline]

    list_display = ["username", "email", "first_name", "last_name", "phone_number", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_superuser", "is_active"]
    search_fields = ["username", "first_name", "last_name", "email", "phone_number"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("اطلاعات شخصی", {"fields": ("first_name", "last_name", "email", "phone_number")}),
        (
            "سطح دسترسی و نقش‌ها",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("تاریخ‌های مهم", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "email",
                    "phone_number",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
