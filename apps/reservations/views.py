from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView

from apps.core.mixins import HtmxMixin
from apps.reservations.exceptions import DomainError

from . import selectors, services
from .forms import ReservaCancelarForm, ReservaFiltroForm, ReservaForm
from .models import Reserva
from django.views.generic.edit import UpdateView


class ReservaListView(LoginRequiredMixin, HtmxMixin, ListView):
    model = Reserva
    context_object_name = 'reservas'
    template_name = 'reservations/lista.html'
    partial_template_name = 'reservations/partials/_tabela_reservas.html'
    paginate_by = 15

    def get_filter_form(self):
        if not hasattr(self, '_filtro_form'):
            data = self.request.POST if self.request.method == 'POST' else self.request.GET
            self._filtro_form = ReservaFiltroForm(data or None)
        return self._filtro_form

    def get_queryset(self):
        qs = selectors.reservas_para_usuario(self.request.user).order_by('-data', '-hora_inicio')
        form = self.get_filter_form()
        if not form.is_valid():
            return qs

        status = form.cleaned_data.get('status')
        data = form.cleaned_data.get('data')
        if status:
            qs = qs.filter(status=status)
        if data:
            qs = qs.filter(data=data)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtro_form'] = self.get_filter_form()
        context['cancelar_form'] = ReservaCancelarForm()
        return context


class ReservaCreateView(LoginRequiredMixin, HtmxMixin, CreateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'reservations/form.html'
    partial_template_name = 'reservations/partials/_form_reserva.html'
    success_url = reverse_lazy('reservations:lista')

    def form_valid(self, form):
        try:
            self.object = services.criar_reserva(
                professor=self.request.user,
                **form.cleaned_data,
            )
        except DomainError as exc:
            form.add_error(None, exc.message)
            return self.form_invalid(form)

        messages.success(self.request, 'Reserva criada com sucesso.')
        if getattr(self.request, 'htmx', False):
            response = HttpResponse(status=204)
            response['HX-Redirect'] = self.get_success_url()
            response['HX-Trigger'] = 'modalClosed'
            return response
        return redirect(self.success_url)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if getattr(self.request, 'htmx', False):
            response['HX-Retarget'] = '#modal-container'
        return response


class ReservaCancelarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        return self._cancelar(request, pk)

    def delete(self, request, pk):
        return self._cancelar(request, pk)

    def _cancelar(self, request, pk):
        reserva = get_object_or_404(selectors.reservas_para_usuario(request.user), pk=pk)
        motivo = (request.POST.get('motivo') or 'Excluída pela interface.').strip()

        try:
            services.cancelar_reserva(
                reserva=reserva,
                usuario=request.user,
                motivo=motivo,
            )
        except DomainError as exc:
            messages.error(request, exc.message)
        except PermissionDenied as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, 'Reserva cancelada.')

        if getattr(request, 'htmx', False):
            return self._render_lista_parcial(request)
        return redirect('reservations:lista')

    def _render_lista_parcial(self, request):
        lista_view = ReservaListView()
        lista_view.setup(request)
        lista_view.object_list = lista_view.get_queryset()
        return render(
            request,
            lista_view.partial_template_name,
            lista_view.get_context_data(),
        )


class ReservaUpdateView(LoginRequiredMixin, HtmxMixin, UpdateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'reservations/form.html'
    partial_template_name = 'reservations/partials/_form_reserva.html'
    success_url = reverse_lazy('reservations:lista')

    def get_object(self, queryset=None):
        return get_object_or_404(selectors.reservas_para_usuario(self.request.user), pk=self.kwargs.get('pk'))

    def form_valid(self, form):
        try:
            # reuse service to update reservation if exists; services.criar_reserva handles creation
            # here we simply save the form instance
            self.object = form.save()
        except DomainError as exc:
            form.add_error(None, exc.message)
            return self.form_invalid(form)

        messages.success(self.request, 'Reserva atualizada com sucesso.')
        if getattr(self.request, 'htmx', False):
            response = HttpResponse(status=204)
            response['HX-Redirect'] = self.get_success_url()
            response['HX-Trigger'] = 'modalClosed'
            return response
        return redirect(self.success_url)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if getattr(self.request, 'htmx', False):
            response['HX-Retarget'] = '#modal-container'
        return response
