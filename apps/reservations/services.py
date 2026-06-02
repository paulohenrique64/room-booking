from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .constants import ReservaStatus
from .exceptions import DomainError
from .models import CancelamentoReserva, Reserva


def validar_reserva(reserva: Reserva) -> None:
    """Executa validações de domínio da reserva."""
    reserva.clean()


def registrar_cancelamento(*, reserva: Reserva, usuario=None, motivo: str) -> CancelamentoReserva:
    cancelamento = CancelamentoReserva.objects.filter(reserva=reserva).first()
    if not cancelamento:
        cancelamento = CancelamentoReserva.objects.create(
            reserva=reserva,
            titulo=motivo,
            cancelado_por=usuario,
        )

    return cancelamento


@transaction.atomic
def criar_reserva(*, professor, sala, data, hora_inicio, hora_fim, titulo) -> Reserva:
    reserva = Reserva(
        professor=professor,
        sala=sala,
        data=data,
        hora_inicio=hora_inicio,
        hora_fim=hora_fim,
        titulo=titulo,
    )
    try:
        validar_reserva(reserva)
    except ValidationError as exc:
        raise DomainError(exc.messages[0] if exc.messages else str(exc)) from exc

    reserva.save()
    return reserva


@transaction.atomic
def atualizar_reserva(*, reserva: Reserva, usuario, sala=None, data=None, hora_inicio=None, hora_fim=None, titulo=None) -> Reserva:
    if not usuario.is_staff and reserva.professor_id != usuario.id:
        raise PermissionDenied('Você só pode editar suas próprias reservas.')

    if reserva.status != ReservaStatus.ATIVA:
        raise DomainError('Não é possível editar uma reserva cancelada ou finalizada.')

    if sala is not None:
        reserva.sala = sala
    if data is not None:
        reserva.data = data
    if hora_inicio is not None:
        reserva.hora_inicio = hora_inicio
    if hora_fim is not None:
        reserva.hora_fim = hora_fim
    if titulo is not None:
        reserva.titulo = titulo

    try:
        validar_reserva(reserva)
    except ValidationError as exc:
        raise DomainError(exc.messages[0] if exc.messages else str(exc)) from exc

    reserva.save()
    return reserva


@transaction.atomic
def cancelar_reserva(*, reserva: Reserva, usuario, motivo: str) -> Reserva:
    if not usuario.is_staff and reserva.professor_id != usuario.id:
        raise PermissionDenied('Você só pode cancelar suas próprias reservas.')

    if reserva.status != ReservaStatus.ATIVA:
        raise DomainError('Somente reservas ativas podem ser canceladas.')

    reserva.status = ReservaStatus.CANCELADA
    reserva.save(update_fields=['status', 'atualizado_em'])
    registrar_cancelamento(
        reserva=reserva,
        usuario=usuario,
        motivo=motivo,
    )
    return reserva
