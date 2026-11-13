from django.urls import path
from . import views
app_name = 'dashboard'
urlpatterns = [
    path('index/',views.DashboardView.as_view(),name='dashboard'),
]