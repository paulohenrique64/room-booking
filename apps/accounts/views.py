from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from apps.core.mixins import HtmxMixin

from .forms import GroupAdminForm, UserAdminForm


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


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


class AccessManagementView(StaffRequiredMixin, TemplateView):
    template_name = 'accounts/access.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(access_context())
        return context


def access_context():
    return {
        'usuarios': User.objects.prefetch_related('groups').order_by('username'),
        'grupos': Group.objects.prefetch_related('permissions').order_by('name'),
    }


def _render_access_panel(request):
    return render(request, 'accounts/partials/_access_panel.html', access_context())


def user_modal(request, pk=None):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse(status=403)

    instance = get_object_or_404(User, pk=pk) if pk else None
    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            if getattr(request, 'htmx', False):
                response = _render_access_panel(request)
                response['HX-Trigger'] = 'modalClosed'
                return response
            return redirect('accounts:access')
    else:
        form = UserAdminForm(instance=instance)

    response = render(request, 'accounts/partials/_form_user.html', {'form': form, 'pk': pk})
    if getattr(request, 'htmx', False) and request.method == 'POST' and not form.is_valid():
        response['HX-Retarget'] = '#modal-container'
    return response


def user_delete(request, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse(status=403)
    if request.method not in ('POST', 'DELETE'):
        return HttpResponse(status=405)

    user = get_object_or_404(User, pk=pk)
    if user.pk == request.user.pk:
        return render(
            request,
            'accounts/partials/_access_panel.html',
            {**access_context(), 'access_error': 'Você não pode excluir seu próprio usuário.'},
        )
    user.delete()
    if getattr(request, 'htmx', False):
        return _render_access_panel(request)
    return redirect('accounts:access')


def group_modal(request, pk=None):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse(status=403)

    instance = get_object_or_404(Group, pk=pk) if pk else None
    if request.method == 'POST':
        form = GroupAdminForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            if getattr(request, 'htmx', False):
                response = _render_access_panel(request)
                response['HX-Trigger'] = 'modalClosed'
                return response
            return redirect('accounts:access')
    else:
        form = GroupAdminForm(instance=instance)

    response = render(request, 'accounts/partials/_form_group.html', {'form': form, 'pk': pk})
    if getattr(request, 'htmx', False) and request.method == 'POST' and not form.is_valid():
        response['HX-Retarget'] = '#modal-container'
    return response


def group_delete(request, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse(status=403)
    if request.method not in ('POST', 'DELETE'):
        return HttpResponse(status=405)

    group = get_object_or_404(Group, pk=pk)
    if group.user_set.exists():
        return render(
            request,
            'accounts/partials/_access_panel.html',
            {**access_context(), 'access_error': 'Não é possível excluir um grupo atribuído a usuários.'},
        )
    group.delete()
    if getattr(request, 'htmx', False):
        return _render_access_panel(request)
    return redirect('accounts:access')
