from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F


class Recurso(models.Model):
    """Recursos disponíveis em salas (projetor, whiteboard, ar-condicionado, etc)."""

    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    quantidade = models.PositiveIntegerField(default=1)
    icone = models.CharField(max_length=50, default='videocam', help_text='Material Symbols icon name')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name_plural = 'Recursos'

    def __str__(self):
        return self.nome

    def delete(self, *args, **kwargs):
        if self.salas.exists():
            raise ValidationError('Não é possível excluir um equipamento em uso por salas.')
        return super().delete(*args, **kwargs)


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

    def clean(self):
        super().clean()
        nome = (self.nome or '').strip()
        predio = (self.predio or '').strip()
        if not nome or not predio:
            return

        duplicada = Sala.objects.filter(nome__iexact=nome, predio__iexact=predio)
        if self.pk:
            duplicada = duplicada.exclude(pk=self.pk)
        if duplicada.exists():
            raise ValidationError({'nome': 'Já existe uma sala com este nome neste prédio.'})

    def delete(self, *args, **kwargs):
        recurso_ids = list(self.recursos.values_list('pk', flat=True))
        deleted = super().delete(*args, **kwargs)
        if recurso_ids:
            Recurso.objects.filter(pk__in=recurso_ids).update(quantidade=F('quantidade') + 1)
        return deleted

    @property
    def image_url(self):
        """Extrai a URL da imagem embutida em `descricao` no formato 'Imagem: {url} | texto'."""
        descricao = (self.descricao or '')
        marker = 'Imagem:'
        if marker not in descricao:
            return ''
        remainder = descricao.split(marker, 1)[1].strip()
        return remainder.split('|', 1)[0].strip()

    @property
    def short_descricao(self):
        """Retorna a parte descritiva sem o marcador de imagem."""
        descricao = (self.descricao or '')
        marker = 'Imagem:'
        if marker not in descricao:
            return descricao
        remainder = descricao.split(marker, 1)[1]
        parts = remainder.split('|', 1)
        if len(parts) == 2:
            return parts[1].strip()
        return ''
