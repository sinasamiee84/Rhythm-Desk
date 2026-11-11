from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from apps.patients.models import Patient, ECGRecord
from apps.patients.services import analyze_ecg
from .forms import PatientForm, ECGRecordForm


class PatientOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """دسترسی فقط به بیمارانِ خودِ پزشک"""

    def test_func(self):
        patient = self.get_object()
        return patient.doctor == self.request.user


class PatientListView(LoginRequiredMixin, ListView):
    model = Patient
    context_object_name = "patients"
    template_name = "patients/list.html"

    def get_queryset(self):
        return (
            Patient.objects
            .filter(doctor=self.request.user)
            .prefetch_related("ecg_records")
        )


class PatientDetailView(PatientOwnerMixin, DetailView):
    model = Patient
    context_object_name = "patient"
    template_name = "patients/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ecg_records"] = self.object.ecg_records.all().order_by("-created_at")
        return context


class CreatePatientView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/create.html"
    success_url = reverse_lazy("patients:list")

    def form_valid(self, form):
        form.instance.doctor = self.request.user
        messages.success(self.request, "بیمار با موفقیت افزوده شد.")
        return super().form_valid(form)


class PatientUpdateView(PatientOwnerMixin, UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/update.html"
    success_url = reverse_lazy("patients:list")

    def form_valid(self, form):
        messages.info(self.request, "اطلاعات بیمار با موفقیت ویرایش شد.")
        return super().form_valid(form)


class DeletePatientView(PatientOwnerMixin, DeleteView):
    model = Patient
    template_name = "patients/confirm_delete.html"
    success_url = reverse_lazy("patients:list")

    def form_valid(self, form):
        messages.warning(self.request, "پرونده بیمار با موفقیت حذف شد.")
        return super().form_valid(form)


class ECGRecordOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """دسترسی فقط به رکوردهای ECG مربوط به بیمارانِ همان پزشک"""

    def test_func(self):
        record = self.get_object()
        return record.patient.doctor == self.request.user


class CreateECGRecordView(LoginRequiredMixin, CreateView):
    model = ECGRecord
    form_class = ECGRecordForm
    template_name = "patients/ecg_form.html"

    def dispatch(self, request, *args, **kwargs):
        # بیمار باید متعلق به پزشک واردشده باشد.
        self.patient = Patient.objects.filter(
            pk=self.kwargs["patient_pk"],
            doctor=request.user,
        ).first()

        if self.patient is None:
            messages.error(
                request,
                "بیمار مورد نظر یافت نشد یا به آن دسترسی ندارید.",
            )
            return redirect("patients:list")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # ابتدا رکورد را ذخیره می‌کنیم تا فایل در storage ثبت شود.
        record = form.save(commit=False)
        record.patient = self.patient
        record.save()

        try:
            # analyze_ecg باید فایل و نرخ نمونه‌برداری را دریافت کند.
            result = analyze_ecg(
                record.signal_file,
                record.sampling_rate,
            )

            if result.get("success"):
                record.bpm = result.get("bpm")
                record.arrhythmia_type = result.get(
                    "arrhythmia_type",
                    "نامشخص",
                )
                record.signal_status = result.get("status", "PENDING")
                record.save(
                    update_fields=[
                        "bpm",
                        "arrhythmia_type",
                        "signal_status",
                    ]
                )
                messages.success(
                    self.request,
                    "فایل ECG بارگذاری و تحلیل شد.",
                )
            else:
                record.signal_status = ECGRecord.SignalStatus.NOISE
                record.arrhythmia_type = result.get(
                    "arrhythmia_type",
                    "تحلیل سیگنال ناموفق بود.",
                )
                record.save(
                    update_fields=[
                        "signal_status",
                        "arrhythmia_type",
                    ]
                )
                messages.warning(
                    self.request,
                    result.get("error", "تحلیل سیگنال انجام نشد."),
                )

        except Exception:
            # خطای تحلیل نباید باعث از دست رفتن فایل بارگذاری‌شده شود.
            record.signal_status = ECGRecord.SignalStatus.NOISE
            record.arrhythmia_type = "خطا در پردازش سیگنال"
            record.save(
                update_fields=[
                    "signal_status",
                    "arrhythmia_type",
                ]
            )
            messages.warning(
                self.request,
                "رکورد ذخیره شد، اما هنگام تحلیل سیگنال خطایی رخ داد.",
            )

        self.object = record
        return redirect(self.get_success_url())

    def get_success_url(self):
        return self.patient.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient"] = self.patient
        return context


class ECGRecordDetailView(ECGRecordOwnerMixin, DetailView):
    model = ECGRecord
    context_object_name = "ecg_record"
    template_name = "patients/ecg_detail.html"


class DeleteECGRecordView(ECGRecordOwnerMixin, DeleteView):
    model = ECGRecord
    template_name = "patients/ecg_confirm_delete.html"

    def get_success_url(self):
        return self.object.patient.get_absolute_url()

    def form_valid(self, form):
        messages.warning(self.request, "رکورد ECG با موفقیت حذف شد.")
        return super().form_valid(form)


class ECGRecordUpdateView(ECGRecordOwnerMixin, UpdateView):
    model = ECGRecord
    form_class = ECGRecordForm
    template_name = "patients/ecg_form.html"

    def get_success_url(self):
        return reverse_lazy(
            "patients:ecg_detail",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        messages.info(self.request, "رکورد ECG با موفقیت ویرایش شد.")
        return super().form_valid(form)

