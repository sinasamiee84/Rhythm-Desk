from django.urls import path
from .views import CustomLogoutView, CustomLoginView, CustomRegisterView, ProfileUpdateView , ChangePasswordView

app_name = 'accounts'
urlpatterns = [
    path('register', CustomRegisterView.as_view(), name='register'),
    path('login', CustomLoginView.as_view(), name='login'),
    path('logout', CustomLogoutView.as_view(), name='logout'),
    path('profile/', ProfileUpdateView.as_view(), name='profile'),
    path('password-change/', ChangePasswordView.as_view(), name='change_password'),
]
