from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from apps.patients.models import Patient
from .forms import PatientForm




class PatientOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """دسترسی فقط به بیمارانِ خودِ پزشک"""
    def test_func(self):
        patient = self.get_object()
        return patient.doctor == self.request.user


class PatientListView(LoginRequiredMixin, ListView):
    model = Patient
    context_object_name = 'patients'
    template_name = 'patients/list.html'

    def get_queryset(self):
        return (
            Patient.objects
            .filter(doctor=self.request.user)
            .prefetch_related('ecg_records')   # ← رکوردهای ECG همراه بیمار
        )


class PatientDetailView(PatientOwnerMixin, DetailView):
    model = Patient
    context_object_name = 'patient'
    template_name = 'patients/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # رکوردهای ECG همین بیمار، جدیدترین اول
        context['ecg_records'] = self.object.ecg_records.all().order_by('-created_at')
        return context

class CreatePatientView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = PatientForm
    template_name = 'patients/create.html' # فایل HTML را درست کن
    success_url = reverse_lazy('patients:list') # آدرس لیست بیماران

    def form_valid(self, form):
        form.instance.doctor = self.request.user # مقداردهی دکتری که ثبت می‌کند
        messages.success(self.request, 'بیمار با موفقیت افزوده شد.')
        return super().form_valid(form)

class PatientUpdateView(PatientOwnerMixin, UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = 'patients/update.html'
    success_url = reverse_lazy('patients:list')

    def form_valid(self, form):
        messages.info(self.request, 'اطلاعات بیمار با موفقیت ویرایش شد.')
        return super().form_valid(form)

class DeletePatientView(PatientOwnerMixin, DeleteView):
    model = Patient
    template_name = 'patients/confirm_delete.html'
    success_url = reverse_lazy('patients:list')

    def form_valid(self, form):
        messages.warning(self.request, 'پرونده بیمار با موفقیت حذف شد.')
        return super().form_valid(form)

