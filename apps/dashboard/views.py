from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.views.generic import TemplateView

from apps.patients.models import Patient, ECGRecord  # نام اپ مدل‌هایت را بگذار


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # تمام بیماران متعلق به همین پزشک
        doctor_patients = Patient.objects.filter(doctor=user)

        # تمام رکوردهای ECG مربوط به بیماران همین پزشک
        doctor_ecgs = ECGRecord.objects.filter(patient__doctor=user)

        # ۱. کارت‌های آمار کلیدی (Key Metrics)
        # تجمیع وضعیت‌ها در یک کوئری سریع با Aggregate
        stats = doctor_ecgs.aggregate(
            total_ecg=Count("id"),
            pending_count=Count("id", filter=Q(signal_status=ECGRecord.SignalStatus.PENDING)),
            arrhythmia_count=Count("id", filter=Q(signal_status=ECGRecord.SignalStatus.ARRHYTHMIA)),
            normal_count=Count("id", filter=Q(signal_status=ECGRecord.SignalStatus.NORMAL)),
            noise_count=Count("id", filter=Q(signal_status=ECGRecord.SignalStatus.NOISE)),
        )

        context["total_patients"] = doctor_patients.count()
        context["total_ecg"] = stats["total_ecg"]
        context["pending_count"] = stats["pending_count"]
        context["arrhythmia_count"] = stats["arrhythmia_count"]
        context["normal_count"] = stats["normal_count"]
        context["noise_count"] = stats["noise_count"]

        # ۲. هشدارهای فوری (آخرین سیگنال‌های آریتمی‌دار برای بررسی پزشک)
        context["critical_alerts"] = (
            doctor_ecgs.filter(signal_status=ECGRecord.SignalStatus.ARRHYTHMIA)
            .select_related("patient")
            .order_by("-created_at")[:5]
        )

        # ۳. آخرین رکوردهای ثبت‌شده (فارغ از وضعیت برای جدول زنده داشبورد)
        context["recent_records"] = (
            doctor_ecgs.select_related("patient")
            .order_by("-created_at")[:6]
        )

        # ۴. آخرین بیماران اضافه‌شده
        context["recent_patients"] = doctor_patients.order_by("-created_at")[:5]

        return context

