"""
Custom querysets and managers para otimização de queries.
"""
from django.db import models
from django.db.models import Count, Q, F
from django.utils import timezone


class ReservaQuerySet(models.QuerySet):
    """QuerySet customizado com métodos de filtro otimizados."""
    
    def ativas(self):
        """Apenas reservas ativas."""
        from .constants import ReservaStatus
        return self.filter(status=ReservaStatus.ATIVA)
    
    def por_usuario(self, usuario):
        """Reservas de um usuário específico."""
        return self.filter(professor=usuario)
    
    def por_sala(self, sala):
        """Reservas de uma sala específica."""
        return self.filter(sala=sala)
    
    def em_data(self, data):
        """Reservas em uma data específica."""
        return self.filter(data=data)
    
    def proximas(self, dias=30):
        """Próximas N dias (default 30), apenas ativas."""
        hoje = timezone.now().date()
        limite = hoje + timezone.timedelta(days=dias)
        return (
            self.ativas()
            .filter(data__gte=hoje, data__lte=limite)
            .order_by('data', 'hora_inicio')
        )
    
    def com_select_related(self):
        """Otimização: eager load de relacionamentos."""
        return self.select_related('sala', 'professor')
    
    def com_professor_info(self):
        """Otimização: add nome completo do professor."""
        return self.annotate(
            nome_professor=F('professor__first_name')
        )


class ReservaManager(models.Manager):
    """Manager para Reserva."""
    
    def get_queryset(self):
        return ReservaQuerySet(self.model, using=self._db)
    
    def ativas(self):
        return self.get_queryset().ativas()
    
    def por_usuario(self, usuario):
        return self.get_queryset().por_usuario(usuario)
    
    def por_sala(self, sala):
        return self.get_queryset().por_sala(sala)
    
    def proximas(self, dias=30):
        return self.get_queryset().proximas(dias=dias)


class SalaQuerySet(models.QuerySet):
    """QuerySet customizado para Sala com otimizações."""
    
    def ativas(self):
        """Apenas salas ativas."""
        return self.filter(ativa=True)
    
    def com_recursos(self):
        """Otimização: prefetch recursos (M2M)."""
        return self.prefetch_related('recursos')
    
    def com_disponibilidade_em_data(self, data):
        """
        Calcula disponibilidade de salas para uma data específica.
        Evita N+1 query usando annotate.
        """
        from .constants import ReservaStatus
        return self.annotate(
            reservas_count=Count(
                'reservas',
                filter=Q(
                    reservas__data=data,
                    reservas__status=ReservaStatus.ATIVA
                )
            )
        )


class SalaManager(models.Manager):
    """Manager para Sala."""
    
    def get_queryset(self):
        return SalaQuerySet(self.model, using=self._db)
    
    def ativas(self):
        return self.get_queryset().ativas()
    
    def com_recursos(self):
        return self.get_queryset().com_recursos()
    
    def com_disponibilidade_em_data(self, data):
        return self.get_queryset().com_disponibilidade_em_data(data)
