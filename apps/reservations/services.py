from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .exceptions import DomainError
from .models import CancelamentoReserva, HistoricoReserva, Reserva


def validar_reserva(reserva: Reserva) -> None:
    """Executa validações de domínio da reserva."""
    reserva.clean()


@transaction.atomic
def criar_reserva(*, professor, sala, data, hora_inicio, hora_fim, motivo) -> Reserva:
    reserva = Reserva(
        professor=professor,
        sala=sala,
        data=data,
        hora_inicio=hora_inicio,
        hora_fim=hora_fim,
        motivo=motivo,
    )
    try:
        validar_reserva(reserva)
    except ValidationError as exc:
        raise DomainError(exc.messages[0] if exc.messages else str(exc)) from exc

    reserva.save()
    HistoricoReserva.objects.create(
        reserva=reserva,
        acao='criada',
        usuario=professor,
        descricao='Reserva criada',
    )
    return reserva


@transaction.atomic
def atualizar_reserva(*, reserva: Reserva, usuario, sala=None, data=None, hora_inicio=None, hora_fim=None, motivo=None) -> Reserva:
    if not usuario.is_staff and reserva.professor_id != usuario.id:
        raise PermissionDenied('Você só pode editar suas próprias reservas.')

    if reserva.status != 'ativa':
        raise DomainError('Não é possível editar uma reserva cancelada ou finalizada.')

    if sala is not None:
        reserva.sala = sala
    if data is not None:
        reserva.data = data
    if hora_inicio is not None:
        reserva.hora_inicio = hora_inicio
    if hora_fim is not None:
        reserva.hora_fim = hora_fim
    if motivo is not None:
        reserva.motivo = motivo

    try:
        validar_reserva(reserva)
    except ValidationError as exc:
        raise DomainError(exc.messages[0] if exc.messages else str(exc)) from exc

    reserva.save()
    HistoricoReserva.objects.create(
        reserva=reserva,
        acao='editada',
        usuario=usuario,
        descricao='Reserva editada',
    )
    return reserva


@transaction.atomic
def cancelar_reserva(*, reserva: Reserva, usuario, motivo: str) -> Reserva:
    if not usuario.is_staff and reserva.professor_id != usuario.id:
        raise PermissionDenied('Você só pode cancelar suas próprias reservas.')

    if reserva.status == 'cancelada':
        raise DomainError('Esta reserva já foi cancelada')

    reserva.status = 'cancelada'
    reserva.save(update_fields=['status', 'atualizado_em'])

    CancelamentoReserva.objects.create(
        reserva=reserva,
        motivo=motivo,
        cancelado_por=usuario,
    )
    HistoricoReserva.objects.create(
        reserva=reserva,
        acao='cancelada',
        usuario=usuario,
        descricao=f'Reserva cancelada: {motivo}',
    )
    return reserva
