from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class Recurso(models.Model):
    """Recursos disponíveis em salas (projetor, whiteboard, ar-condicionado, etc)"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name_plural = 'Recursos'

    def __str__(self):
        return self.nome


class Sala(models.Model):
    """Salas da universidade disponíveis para agendamento"""
    nome = models.CharField(max_length=100)
    predio = models.CharField(max_length=100)
    andar = models.IntegerField()
    capacidade = models.PositiveIntegerField()
    descricao = models.TextField(blank=True)
    recursos = models.ManyToManyField(Recurso, blank=True, related_name='salas')
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['predio', 'andar', 'nome']
        verbose_name_plural = 'Salas'
        unique_together = ['predio', 'andar', 'nome']
        indexes = [
            models.Index(fields=['ativa', 'predio']),
            models.Index(fields=['capacidade']),
        ]

    def __str__(self):
        return f'{self.nome} - {self.predio} ({self.capacidade} pessoas)'


class Reserva(models.Model):
    """Reservas de salas por professores"""
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('cancelada', 'Cancelada'),
        ('finalizada', 'Finalizada'),
    ]

    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name='reservas')
    professor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas')
    data = models.DateField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    motivo = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativa')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data', '-hora_inicio']
        verbose_name_plural = 'Reservas'
        indexes = [
            models.Index(fields=['sala', 'data', 'hora_inicio']),
            models.Index(fields=['professor', 'data']),
            models.Index(fields=['data', 'status']),
        ]

    def __str__(self):
        return f'{self.sala.nome} - {self.data} ({self.hora_inicio} a {self.hora_fim})'

    def clean(self):
        """Validação de negócio:
        - Horário de fim não pode ser antes ou igual ao de início
        - Não pode ter conflito com outras reservas ativas na mesma sala
        - Não pode fazer reserva para datas passadas
        """
        if self.hora_fim <= self.hora_inicio:
            raise ValidationError('Horário de fim deve ser posterior ao horário de início.')

        if self.data < timezone.now().date():
            raise ValidationError('Não é possível fazer reservas para datas passadas.')

        # Detectar conflitos com reservas ativas
        conflitos = Reserva.objects.filter(
            sala=self.sala,
            data=self.data,
            status='ativa'
        ).exclude(pk=self.pk)

        for reserva in conflitos:
            # Verificar sobreposição de horários
            if not (self.hora_fim <= reserva.hora_inicio or self.hora_inicio >= reserva.hora_fim):
                raise ValidationError(
                    f'Conflito de horário! A sala já está reservada de {reserva.hora_inicio} a {reserva.hora_fim}.'
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class CancelamentoReserva(models.Model):
    """Rastreamento de cancelamentos de reservas"""
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='cancelamento')
    motivo = models.TextField()
    cancelado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cancelamentos_realizados')
    data_cancelamento = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Cancelamentos de Reservas'

    def __str__(self):
        return f'Cancelamento de {self.reserva} - {self.data_cancelamento.date()}'


class HistoricoReserva(models.Model):
    """Auditoria completa de ações em reservas"""
    ACAO_CHOICES = [
        ('criada', 'Criada'),
        ('cancelada', 'Cancelada'),
        ('editada', 'Editada'),
        ('finalizada', 'Finalizada'),
    ]

    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='historico')
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES)
    descricao = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name_plural = 'Históricos de Reserva'
        indexes = [
            models.Index(fields=['reserva', 'data_hora']),
        ]

    def __str__(self):
        return f'{self.reserva} - {self.acao} ({self.data_hora.date()})'

