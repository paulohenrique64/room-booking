from django.db import models


class Recurso(models.Model):
    """Recursos disponíveis em salas (projetor, whiteboard, ar-condicionado, etc)."""

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
    """Salas da universidade disponíveis para agendamento."""

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
