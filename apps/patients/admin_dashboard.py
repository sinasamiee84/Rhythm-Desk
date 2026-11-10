from django.db.models import Count, Q

from .models import ECGRecord, Patient


def dashboard_callback(request, context):
    if request.user.is_superuser:
        patients = Patient.objects.all()
        records = ECGRecord.objects.all()
    else:
        patients = Patient.objects.filter(doctor=request.user)
        records = ECGRecord.objects.filter(
            patient__doctor=request.user
        )

    totals = records.aggregate(
        total=Count("pk"),
        pending=Count(
            "pk",
            filter=Q(signal_status=ECGRecord.SignalStatus.PENDING),
        ),
        normal=Count(
            "pk",
            filter=Q(signal_status=ECGRecord.SignalStatus.NORMAL),
        ),
        arrhythmia=Count(
            "pk",
            filter=Q(signal_status=ECGRecord.SignalStatus.ARRHYTHMIA),
        ),
        noise=Count(
            "pk",
            filter=Q(signal_status=ECGRecord.SignalStatus.NOISE),
        ),
    )

    context["stats"] = {
        "patients": patients.count(),
        "records": totals["total"],
        # رکورد نویزی هم نتیجهٔ پردازش دارد؛ «در انتظار» ندارد.
        "processed": totals["total"] - totals["pending"],
        "pending": totals["pending"],
        "normal": totals["normal"],
        "arrhythmia": totals["arrhythmia"],
        "noise": totals["noise"],
    }

    context["recent_records"] = (
        records.select_related("patient")
        .order_by("-created_at")[:5]
    )

    return context
