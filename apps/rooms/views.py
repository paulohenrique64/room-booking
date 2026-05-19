from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView

from apps.core.mixins import HtmxMixin
from apps.reservations import selectors

from .models import Sala


class SalaListView(LoginRequiredMixin, HtmxMixin, ListView):
    model = Sala
    context_object_name = 'salas'
    template_name = 'rooms/lista.html'
    partial_template_name = 'rooms/partials/_lista_salas.html'
    paginate_by = 12

    def get_queryset(self):
        return selectors.salas_ativas()


class SalaDetailView(LoginRequiredMixin, HtmxMixin, DetailView):
    model = Sala
    context_object_name = 'sala'
    template_name = 'rooms/detalhe.html'
    partial_template_name = 'rooms/partials/_disponibilidade.html'

    def get_queryset(self):
        return selectors.salas_ativas()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data_str = self.request.GET.get('data')
        if data_str:
            try:
                data = datetime.strptime(data_str, '%Y-%m-%d').date()
                context['disponibilidade'] = selectors.disponibilidade_sala(self.object, data)
            except ValueError:
                context['erro_data'] = 'Data inválida. Use YYYY-MM-DD.'
        return context
