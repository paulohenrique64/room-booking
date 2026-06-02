from datetime import datetime

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.rooms.api.serializers import SalaSerializer
from apps.rooms.models import Sala
from apps.reservations.constants import ReservaStatus
from apps.reservations import services

from apps.reservations.exceptions import DomainError
from apps.reservations.models import CancelamentoReserva, Reserva


class CancelamentoReservaSerializer(serializers.ModelSerializer):
    cancelado_por = UserSerializer(read_only=True)
    motivo = serializers.CharField(source='titulo')
    data_cancelamento_local = serializers.SerializerMethodField()
    data_cancelamento_formatada = serializers.SerializerMethodField()

    class Meta:
        model = CancelamentoReserva
        fields = [
            'id', 'motivo', 'cancelado_por', 'data_cancelamento',
            'data_cancelamento_local', 'data_cancelamento_formatada',
        ]

    def get_data_cancelamento_local(self, obj):
        return timezone.localtime(obj.data_cancelamento).isoformat()

    def get_data_cancelamento_formatada(self, obj):
        return timezone.localtime(obj.data_cancelamento).strftime('%d/%m/%Y %H:%M')


class ReservaSerializer(serializers.ModelSerializer):
    sala = SalaSerializer(read_only=True)
    professor = UserSerializer(read_only=True)
    cancelamento = CancelamentoReservaSerializer(read_only=True)
    duracao = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Reserva
        fields = [
            'id', 'sala', 'professor', 'data', 'hora_inicio', 'hora_fim',
            'titulo', 'status', 'status_display', 'duracao',
            'cancelamento', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['professor', 'criado_em', 'atualizado_em']

    def get_duracao(self, obj):
        inicio = datetime.combine(obj.data, obj.hora_inicio)
        fim = datetime.combine(obj.data, obj.hora_fim)
        duracao_minutos = int((fim - inicio).total_seconds() / 60)
        horas = duracao_minutos // 60
        minutos = duracao_minutos % 60
        return f'{horas}h {minutos}min' if horas > 0 else f'{minutos}min'


class ReservaCreateUpdateSerializer(serializers.ModelSerializer):
    sala = serializers.PrimaryKeyRelatedField(queryset=Sala.objects.filter(ativa=True))

    class Meta:
        model = Reserva
        fields = ['sala', 'data', 'hora_inicio', 'hora_fim', 'titulo']

    def validate(self, data):
        instance = getattr(self, 'instance', None)
        reserva = Reserva(
            sala=data.get('sala', getattr(instance, 'sala', None)),
            data=data.get('data', getattr(instance, 'data', None)),
            hora_inicio=data.get('hora_inicio', getattr(instance, 'hora_inicio', None)),
            hora_fim=data.get('hora_fim', getattr(instance, 'hora_fim', None)),
            titulo=data.get('titulo', getattr(instance, 'titulo', '')),
            professor=getattr(instance, 'professor', self.context['request'].user),
            status=getattr(instance, 'status', ReservaStatus.ATIVA),
        )
        if instance is not None:
            reserva.pk = instance.pk

        try:
            services.validar_reserva(reserva)
        except DomainError as exc:
            raise serializers.ValidationError(exc.message) from exc
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return data


class ReservaCancelSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=255, required=True)
