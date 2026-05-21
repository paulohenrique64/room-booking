"""
Constantes para o app de reservas.
Evita strings mágicas e facilita refatoração.
"""
from django.db import models


class ReservaStatus(models.TextChoices):
    """Status possíveis de uma reserva."""
    ATIVA = 'ativa', 'Ativa'
    CANCELADA = 'cancelada', 'Cancelada'
    FINALIZADA = 'finalizada', 'Finalizada'


class HistoricoAcao(models.TextChoices):
    """Ações registradas no histórico de reservas."""
    CRIADA = 'criada', 'Criada'
    CANCELADA = 'cancelada', 'Cancelada'
    EDITADA = 'editada', 'Editada'
    FINALIZADA = 'finalizada', 'Finalizada'
