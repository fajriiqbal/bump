from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from .forms import LoginForm, PondokProfileForm
from .models import PondokProfile


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session["show_welcome_toast"] = True
        return response


def custom_logout_view(request):
    logout(request)
    return redirect(reverse_lazy("accounts:login"))


class PondokProfileSetupView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PondokProfile
    form_class = PondokProfileForm
    template_name = "accounts/profile_setup.html"
    success_url = reverse_lazy("dashboard:home")

    def test_func(self):
        user = self.request.user
        return user.is_superuser or getattr(user, "role", "") == "admin"

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return PondokProfile.get_solo()

    def form_valid(self, form):
        messages.success(self.request, "Profil pondok berhasil disimpan.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Profil Pondok"
        context["profile_ready"] = self.get_object().is_complete()
        return context
