from datetime import datetime

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.rooms.api.serializers import SalaSerializer
from apps.reservations import services
from apps.reservations.exceptions import DomainError
from apps.reservations.models import CancelamentoReserva, HistoricoReserva, Reserva


class HistoricoReservaSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    acao_display = serializers.CharField(source='get_acao_display', read_only=True)

    class Meta:
        model = HistoricoReserva
        fields = ['id', 'acao', 'acao_display', 'usuario', 'data_hora', 'descricao']


class CancelamentoReservaSerializer(serializers.ModelSerializer):
    cancelado_por = UserSerializer(read_only=True)

    class Meta:
        model = CancelamentoReserva
        fields = ['id', 'motivo', 'cancelado_por', 'data_cancelamento']


class ReservaSerializer(serializers.ModelSerializer):
    sala = SalaSerializer(read_only=True)
    professor = UserSerializer(read_only=True)
    historico = HistoricoReservaSerializer(many=True, read_only=True)
    cancelamento = CancelamentoReservaSerializer(read_only=True)
    duracao = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Reserva
        fields = [
            'id', 'sala', 'professor', 'data', 'hora_inicio', 'hora_fim',
            'motivo', 'status', 'status_display', 'duracao', 'historico',
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
    class Meta:
        model = Reserva
        fields = ['sala', 'data', 'hora_inicio', 'hora_fim', 'motivo']

    def validate(self, data):
        reserva = Reserva(**data, professor=self.context['request'].user)
        try:
            services.validar_reserva(reserva)
        except DomainError as exc:
            raise serializers.ValidationError(exc.message) from exc
        return data


class ReservaCancelSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=255, required=True)
