from django.urls import path

from .views import (
    PatientListView,
    PatientDetailView,
    CreatePatientView,
    PatientUpdateView,
    DeletePatientView,
)

app_name = "patients"

urlpatterns = [
    path("", PatientListView.as_view(), name="list"),
    path("create/", CreatePatientView.as_view(), name="create"),
    path("<int:pk>/", PatientDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", PatientUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", DeletePatientView.as_view(), name="delete"),
]
