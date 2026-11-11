from django.urls import path
from .views import (
    PatientListView,
    PatientDetailView,
    CreatePatientView,
    PatientUpdateView,
    DeletePatientView,
    CreateECGRecordView,
    ECGRecordDetailView,
    DeleteECGRecordView,
ECGRecordUpdateView
)

app_name = "patients"

urlpatterns = [
    # مسیرهای بیماران
    path("", PatientListView.as_view(), name="list"),
    path("create/", CreatePatientView.as_view(), name="create"),
    path("<int:pk>/", PatientDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", PatientUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", DeletePatientView.as_view(), name="delete"),

    # مسیرهای ECG Records (مطبق با detail.html)
    path("patient/<int:patient_pk>/ecg/add/", CreateECGRecordView.as_view(), name="ecg_create"),
    path("ecg/<int:pk>/", ECGRecordDetailView.as_view(), name="ecg_detail"),
    path("ecg/<int:pk>/edit/", ECGRecordUpdateView.as_view(), name="ecg_update"),
    path("ecg/<int:pk>/delete/", DeleteECGRecordView.as_view(), name="ecg_delete"),
]

