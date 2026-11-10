from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages
from django.contrib.auth import login
from unfold.forms import UserCreationForm  # فرم ثبت‌نام سازگار با تم Unfold

from apps.accounts.models import User


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    # اگر از قبل لاگین کرده بود، نذار دوباره فرم لاگین رو ببینه
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('patients:list')


class CustomLogoutView(LogoutView):
    # در جنگو 5 نیازی به LoginRequiredMixin برای لاگ‌اوت نیست
    next_page = reverse_lazy('accounts:login')


class CustomRegisterView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('patients:list')

    def form_valid(self, form):
        # ذخیره یوزر
        response = super().form_valid(form)
        # لاگین خودکار بلافاصله بعد از ثبت‌نام (اختیاری اما کاربرپسند)
        login(self.request, self.object)
        messages.success(self.request, 'اکانت شما با موفقیت ساخته شد و وارد شدید.')
        return response
