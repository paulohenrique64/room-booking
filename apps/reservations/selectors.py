from datetime import date, timedelta

from django.utils import timezone

from apps.rooms.models import Sala

from .models import Reserva


def reservas_para_usuario(usuario):
    """Queryset base de reservas visíveis ao usuário."""
    qs = Reserva.objects.select_related('sala', 'professor')
    if usuario.is_staff:
        return qs
    return qs.filter(professor=usuario)


def horarios_bloqueados(sala, data: date):
    """Retorna lista de horários ocupados para uma sala em uma data."""
    reservas = (
        Reserva.objects.filter(sala=sala, data=data, status='ativa')
        .select_related('professor')
        .order_by('hora_inicio')
    )
    return [
        {
            'inicio': r.hora_inicio,
            'fim': r.hora_fim,
            'inicio_str': str(r.hora_inicio),
            'fim_str': str(r.hora_fim),
            'professor': r.professor.get_full_name() or r.professor.username,
        }
        for r in reservas
    ]


def disponibilidade_sala(sala, data: date):
    """Dados de disponibilidade de uma sala para API e templates."""
    bloqueados = horarios_bloqueados(sala, data)
    return {
        'sala': sala,
        'data': data,
        'horarios_bloqueados': bloqueados,
        'disponivel': len(bloqueados) == 0,
    }


def proximas_reservas_usuario(usuario, dias=30):
    hoje = timezone.now().date()
    return (
        reservas_para_usuario(usuario)
        .filter(data__gte=hoje, data__lte=hoje + timedelta(days=dias), status='ativa')
        .order_by('data', 'hora_inicio')
    )


def salas_ativas():
    return Sala.objects.filter(ativa=True).prefetch_related('recursos')
