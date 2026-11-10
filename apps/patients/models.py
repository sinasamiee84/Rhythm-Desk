from django.db import models
from django.conf import settings

from django.conf import settings
from django.core.validators import MaxValueValidator, RegexValidator
from django.db import models
from django.urls import reverse


class Patient(models.Model):
    GENDER_CHOICES = (
        ('M', 'مرد'),
        ('F', 'زن'),
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="patients",
        verbose_name="پزشک",
    )
    first_name = models.CharField("نام", max_length=100)
    last_name = models.CharField("نام خانوادگی", max_length=100)
    age = models.PositiveSmallIntegerField(
        "سن",
        validators=[MaxValueValidator(130)],
    )
    national_id = models.CharField(
        "کد ملی",
        max_length=10,
        validators=[
            RegexValidator(
                regex=r"^[0-9]{10}$",
                message="کد ملی باید دقیقاً ۱۰ رقم انگلیسی باشد.",
            )
        ],
    )
    medical_history = models.TextField("سوابق پزشکی", blank=True)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)
    phone_number = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M', verbose_name='جنسیت')  # <-- این فیلد اضافه شود

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "بیمار"
        verbose_name_plural = "بیماران"
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "national_id"],
                name="unique_patient_national_id_per_doctor",
            )
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse("patients:detail", kwargs={"pk": self.pk})


class ECGRecord(models.Model):
    class SignalStatus(models.TextChoices):
        PENDING = "PENDING", "در انتظار پردازش"
        NORMAL = "NORMAL", "نرمال"
        ARRHYTHMIA = "ARRHYTHMIA", "آریتمی"
        NOISE = "NOISE", "نویز شدید / نامعتبر"

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="ecg_records",
        verbose_name="بیمار",
    )
    signal_file = models.FileField(
        "فایل سیگنال CSV",
        upload_to="ecg_signals/",
    )
    sampling_rate = models.PositiveIntegerField(
        "فرکانس نمونه‌برداری (Hz)",
        default=250,
    )

    # نتایج تحلیل (پس از پردازش با Pandas پر می‌شوند)
    bpm = models.PositiveSmallIntegerField("ضربان قلب (BPM)", null=True, blank=True)
    arrhythmia_type = models.CharField("نوع آریتمی", max_length=100, blank=True, default="نامشخص")
    signal_status = models.CharField(
        "وضعیت سیگنال",
        max_length=20,
        choices=SignalStatus.choices,
        default=SignalStatus.PENDING,
    )

    created_at = models.DateTimeField("تاریخ ثبت رکورد", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "رکورد ECG"
        verbose_name_plural = "رکوردهای ECG"

    def __str__(self):
        return f"رکورد {self.pk} برای {self.patient}"
