from django.contrib import admin
from django.core.exceptions import PermissionDenied
from unfold.admin import ModelAdmin

from .models import ECGRecord, Patient


class DoctorOwnedAdminMixin:
    """
    محدودسازی فهرست و دسترسی مستقیم به پرونده‌ها بر اساس پزشک.
    هر کلاس مقدار owner_filter خودش را تعیین می‌کند.
    """
    owner_filter = None

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(**{self.owner_filter: request.user})

    def owns_object(self, request, obj):
        if obj is None or request.user.is_superuser:
            return True

        if isinstance(obj, Patient):
            return obj.doctor_id == request.user.pk

        return obj.patient.doctor_id == request.user.pk

    def has_view_permission(self, request, obj=None):
        return (
            super().has_view_permission(request, obj)
            and self.owns_object(request, obj)
        )

    def has_change_permission(self, request, obj=None):
        return (
            super().has_change_permission(request, obj)
            and self.owns_object(request, obj)
        )

    def has_delete_permission(self, request, obj=None):
        return (
            super().has_delete_permission(request, obj)
            and self.owns_object(request, obj)
        )


@admin.register(Patient)
class PatientAdmin(DoctorOwnedAdminMixin, ModelAdmin):
    owner_filter = "doctor"
    actions = None  # جلوگیری از حذف گروهی ناخواسته

    list_display = (
        "full_name",
        "age",
        "national_id",
        "doctor",
        "created_at",
    )
    search_fields = ("first_name", "last_name", "national_id")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    list_per_page = 20

    fields = (
        "doctor",
        "first_name",
        "last_name",
        "age",
        "national_id",
        "medical_history",
        "created_at",
        "updated_at",
    )

    @admin.display(description="نام بیمار")
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_readonly_fields(self, request, obj=None):
        fields = ("created_at", "updated_at")

        # پزشک نمی‌تواند مالک پرونده را از طریق فرم تغییر دهد.
        if not request.user.is_superuser:
            fields += ("doctor",)

        return fields

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.doctor = request.user
        super().save_model(request, obj, form, change)


@admin.register(ECGRecord)
class ECGRecordAdmin(DoctorOwnedAdminMixin, ModelAdmin):
    owner_filter = "patient__doctor"
    actions = None

    list_display = (
        "id",
        "patient",
        "sampling_rate",
        "bpm",
        "arrhythmia_type",
        "signal_status",
        "created_at",
    )
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "patient__national_id",
    )
    list_filter = ("signal_status", "created_at")
    list_select_related = ("patient",)
    ordering = ("-created_at",)
    list_per_page = 20

    fields = (
        "patient",
        "signal_file",
        "sampling_rate",
        "bpm",
        "arrhythmia_type",
        "signal_status",
        "created_at",
    )

    def get_readonly_fields(self, request, obj=None):
        fields = (
            "bpm",
            "arrhythmia_type",
            "signal_status",
            "created_at",
        )

        # رکوردِ ثبت‌شده به بیمار دیگری منتقل نشود.
        if obj is not None:
            fields += ("patient",)

        return fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "patient" and not request.user.is_superuser:
            kwargs["queryset"] = Patient.objects.filter(
                doctor=request.user
            )

        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )

    def save_model(self, request, obj, form, change):
        if (
            not request.user.is_superuser
            and obj.patient.doctor_id != request.user.pk
        ):
            raise PermissionDenied("به این بیمار دسترسی ندارید.")

        super().save_model(request, obj, form, change)
