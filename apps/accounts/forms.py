from django import forms
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, HTML
from .models import Profile

User = get_user_model()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'ایمیل',
            'phone_number': 'شماره تماس',
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'medical_license_number', 'specialty', 'bio']
        labels = {
            'avatar': 'تصویر پروفایل',
            'medical_license_number': 'شماره نظام پزشکی',
            'specialty': 'تخصص',
            'bio': 'درباره پزشک / بیوگرافی',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # فرم‌ها را در یک ویو با هم رندر می‌کنیم
