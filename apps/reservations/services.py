import logging
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.core.exceptions import DomainError
from .constants import ReservaStatus, HistoricoAcao
from .models import CancelamentoReserva, HistoricoReserva, Reserva

logger = logging.getLogger(__name__)


def validar_reserva(reserva: Reserva) -> None:
    """Executa validações de domínio da reserva."""
    reserva.clean()


@transaction.atomic
def criar_reserva(*, professor, sala, data, hora_inicio, hora_fim, motivo) -> Reserva:
    logger.info(f"Criando reserva para {professor.username} em {sala.nome}")
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
        logger.warning(f"Validação falhou para reserva: {exc.messages}")
        raise DomainError(exc.messages[0] if exc.messages else str(exc)) from exc

    reserva.save()
    HistoricoReserva.objects.create(
        reserva=reserva,
        acao=HistoricoAcao.CRIADA,
        usuario=professor,
        descricao='Reserva criada',
    )
    logger.info(f"Reserva #{reserva.id} criada com sucesso")
    return reserva


@transaction.atomic
def atualizar_reserva(*, reserva: Reserva, usuario, sala=None, data=None, hora_inicio=None, hora_fim=None, motivo=None) -> Reserva:
    logger.info(f"Atualizando reserva #{reserva.id} por {usuario.username}")
    
    if not usuario.is_staff and reserva.professor_id != usuario.id:
        logger.warning(f"Permissão negada: {usuario.username} tentou editar reserva de outro usuário")
        raise PermissionDenied('Você só pode editar suas próprias reservas.')

    if reserva.status != ReservaStatus.ATIVA:
        logger.warning(f"Tentativa de editar reserva cancelada/finalizada: #{reserva.id}")
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
        logger.warning(f"Validação falhou ao atualizar reserva #{reserva.id}: {exc.messages}")
        raise DomainError(exc.messages[0] if exc.messages else str(exc)) from exc

    reserva.save()
    HistoricoReserva.objects.create(
        reserva=reserva,
        acao=HistoricoAcao.EDITADA,
        usuario=usuario,
        descricao='Reserva editada',
    )
    logger.info(f"Reserva #{reserva.id} atualizada com sucesso")
    return reserva


@transaction.atomic
def cancelar_reserva(*, reserva: Reserva, usuario, motivo: str) -> Reserva:
    logger.info(f"Cancelando reserva #{reserva.id} por {usuario.username}")
    
    if not usuario.is_staff and reserva.professor_id != usuario.id:
        logger.warning(f"Permissão negada: {usuario.username} tentou cancelar reserva de outro usuário")
        raise PermissionDenied('Você só pode cancelar suas próprias reservas.')

    if reserva.status == ReservaStatus.CANCELADA:
        logger.warning(f"Tentativa de cancelar reserva já cancelada: #{reserva.id}")
        raise DomainError('Esta reserva já foi cancelada')

    reserva.status = ReservaStatus.CANCELADA
    reserva.save(update_fields=['status', 'atualizado_em'])

    CancelamentoReserva.objects.create(
        reserva=reserva,
        motivo=motivo,
        cancelado_por=usuario,
    )
    HistoricoReserva.objects.create(
        reserva=reserva,
        acao=HistoricoAcao.CANCELADA,
        usuario=usuario,
        descricao=f'Reserva cancelada: {motivo}',
    )
    logger.info(f"Reserva #{reserva.id} cancelada com sucesso")
    return reserva
