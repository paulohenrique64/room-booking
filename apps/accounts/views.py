from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from apps.core.mixins import HtmxMixin


class LoginView(HtmxMixin, AuthLoginView):
    template_name = 'accounts/login.html'
    partial_template_name = 'accounts/partials/_login_form.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('reservations:lista')


class LogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


class ProfileView(HtmxMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.request.user
        return context
