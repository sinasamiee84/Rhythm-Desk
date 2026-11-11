import os
from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, HTML
from .models import Patient, ECGRecord


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'age', 'gender', 'national_id', 'phone_number','medical_history']
        widgets = {
            'medical_history': forms.Textarea(attrs={'rows': 4, 'placeholder': 'سوابق بیماری، داروها، جراحی‌ها و ...'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # کلاس دکمه ثبت (همان رنگ سبزآبی پروژه)
        self.helper.add_input(Submit('submit', 'ثبت بیمار', css_class='btn btn-success w-100'))

        # اختیاری: چیدمان حرفه‌ای‌تر فرم (مثلا دو ستونه)
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6'),
                Column('last_name', css_class='form-group col-md-6'),
            ),
            Row(
                Column('age', css_class='form-group col-md-6'),
                Column('gender', css_class='form-group col-md-6'),
            ),
            'national_id',
            'phone_number',
            'medical_history',
        )

class ECGRecordForm(forms.ModelForm):
    class Meta:
        model = ECGRecord
        fields = ['signal_file', 'sampling_rate']
        labels = {
            'signal_file': 'فایل سیگنال ECG (CSV)',
            'sampling_rate': 'فرکانس نمونه‌برداری (Hz)',
        }
        help_texts = {
            'signal_file': 'فایل داده‌های سیگنال با پسوند .csv را بارگذاری کنید.',
            'sampling_rate': 'به‌عنوان مثال: 250 یا 360 هرتز',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # برای فرم‌هایی که آپلود فایل دارند حتماً باید enctype تنظیم باشد
        self.helper.form_tag = True
        self.helper.attrs = {'enctype': 'multipart/form-data'}

        self.helper.layout = Layout(
            Row(
                Column('sampling_rate', css_class='form-group col-md-12 mb-3'),
            ),
            Row(
                Column('signal_file', css_class='form-group col-md-12 mb-3'),
            ),
            HTML('<div class="d-grid mt-3">'),
            Submit('submit', 'بارگذاری و شروع پردازش سیگنال', css_class='btn btn-success btn-lg shadow-sm'),
            HTML('</div>')
        )

    def clean_signal_file(self):
        uploaded_file = self.cleaned_data.get('signal_file')
        if uploaded_file:
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            valid_extensions = ['.csv', '.txt']
            if ext not in valid_extensions:
                raise ValidationError('فرمت فایل مجاز نیست. لطفاً یک فایل CSV یا TXT معتبر بارگذاری کنید.')
        return uploaded_file
