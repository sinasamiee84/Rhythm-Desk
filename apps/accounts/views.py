from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import login
from .forms import ProfileUpdateForm, UserUpdateForm
from .models import Profile
from unfold.forms import UserCreationForm  # فرم ثبت‌نام سازگار با تم Unfold

from apps.accounts.models import User, Profile
from .forms import ProfileUpdateForm

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('patients:list')


class CustomLogoutView(LogoutView):

    next_page = reverse_lazy('accounts:login')


class CustomRegisterView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('patients:list')

    def form_valid(self, form):
        # ذخیره یوزر
        response = super().form_valid(form)

        login(self.request, self.object)
        messages.success(self.request, 'اکانت شما با موفقیت ساخته شد و وارد شدید.')
        return response
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    second_form_class = UserUpdateForm   # فرم ویرایش اطلاعات پایه کاربر
    template_name = 'accounts/update_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        # همیشه پروفایلِ خودِ کاربرِ لاگین‌شده را برمی‌گرداند، بدون نیاز به pk
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['user_form'] = UserUpdateForm(
                self.request.POST,
                instance=self.request.user
            )
        else:
            context['user_form'] = UserUpdateForm(instance=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        profile_form = self.get_form()
        user_form = UserUpdateForm(request.POST, instance=request.user)
        if profile_form.is_valid() and user_form.is_valid():
            return self.form_valid(profile_form, user_form)
        else:
            return self.form_invalid(profile_form, user_form)

    def form_valid(self, profile_form, user_form):
        profile_form.save()
        user_form.save()
        return super().form_valid(profile_form)

class ChangePasswordView(LoginRequiredMixin,SuccessMessageMixin,PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:profile')
    success_message = 'رمز عبور شما با موفقیت تغییر یافت'
