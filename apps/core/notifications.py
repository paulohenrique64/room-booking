from datetime import datetime, timedelta

from django.utils import timezone

from apps.reservations import selectors as reservation_selectors
from apps.reservations.constants import ReservaStatus

from .models import NotificationDismissal


def build_notification_summary(user, *, limit=5):
    if not getattr(user, 'is_authenticated', False):
        return {'items': [], 'new_count': 0}

    now = timezone.localtime()
    soon_limit = now + timedelta(minutes=30)
    reservations = (
        reservation_selectors.reservas_para_usuario(user)
        .filter(status=ReservaStatus.ATIVA, data__gte=now.date())
        .select_related('sala', 'professor')
        .order_by('data', 'hora_inicio')
    )
    dismissed_keys = set(
        NotificationDismissal.objects.filter(user=user).values_list('reservation_id', 'kind')
    )

    items = []
    seen_ids = set()
    for reserva in reservations:
        kind = 'soon'
        if (reserva.id, kind) in dismissed_keys:
            continue
        start_at = timezone.make_aware(
            datetime.combine(reserva.data, reserva.hora_inicio),
            timezone.get_current_timezone(),
        )
        if now <= start_at <= soon_limit:
            minutes = max(1, round((start_at - now).total_seconds() / 60))
            items.append(
                {
                    'id': reserva.id,
                    'kind': kind,
                    'icon': 'calendar_today',
                    'color': 'text-[#ff8a00]',
                    'message': f'Sua reserva "{reserva.titulo}" começa em {minutes} min.',
                }
            )
            seen_ids.add(reserva.id)

    for reserva in reservations:
        if reserva.id in seen_ids:
            continue
        kind = 'scheduled'
        if (reserva.id, kind) in dismissed_keys:
            continue
        professor = reserva.professor.get_full_name() or reserva.professor.username
        is_owner = reserva.professor_id == user.id
        if is_owner:
            message = f'Reserva "{reserva.titulo}" agendada em {reserva.sala.nome}.'
            icon = 'info'
            color = 'text-primary-base'
        else:
            message = f'{reserva.sala.nome} foi reservada por {professor}.'
            icon = 'check'
            color = 'text-secondary-base'

        items.append(
            {
                'id': reserva.id,
                'kind': kind,
                'icon': icon,
                'color': color,
                'message': message,
            }
        )
        seen_ids.add(reserva.id)
        if len(items) >= limit:
            break

    return {
        'items': items[:limit],
        'new_count': len(items[:limit]),
    }


def dismiss_notification(user, *, reservation_id, kind):
    if not getattr(user, 'is_authenticated', False):
        return None
    return NotificationDismissal.objects.get_or_create(
        user=user,
        reservation_id=reservation_id,
        kind=kind,
    )[0]
