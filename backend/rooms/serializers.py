from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Recurso, Sala, Reserva, CancelamentoReserva, HistoricoReserva


class RecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recurso
        fields = ['id', 'nome', 'descricao', 'ativo']


class SalaSerializer(serializers.ModelSerializer):
    recursos = RecursoSerializer(many=True, read_only=True)
    localizacao = serializers.SerializerMethodField()

    class Meta:
        model = Sala
        fields = ['id', 'nome', 'predio', 'andar', 'capacidade', 'descricao', 'recursos', 'ativa', 'localizacao']

    def get_localizacao(self, obj):
        return f'{obj.predio} - Andar {obj.andar}'


class UserSerializer(serializers.ModelSerializer):
    nome_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'nome_completo']

    def get_nome_completo(self, obj):
        return obj.get_full_name() or obj.username


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
            'cancelamento', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['professor', 'criado_em', 'atualizado_em']

    def get_duracao(self, obj):
        from datetime import datetime
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
        from django.core.exceptions import ValidationError
        temp_reserva = Reserva(**data, professor=self.context['request'].user)
        try:
            temp_reserva.clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.message)
        return data


class ReservaCancelSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=255, required=True)


class SalaListSerializer(serializers.ModelSerializer):
    """Serializer otimizado para listagem de salas com disponibilidade"""
    recursos = RecursoSerializer(many=True, read_only=True)
    disponibilidade = serializers.SerializerMethodField()

    class Meta:
        model = Sala
        fields = ['id', 'nome', 'predio', 'andar', 'capacidade', 'recursos', 'disponibilidade']

    def get_disponibilidade(self, obj):
        # Se a data foi passada nos query params, calcula disponibilidade
        request = self.context.get('request')
        if request and 'data' in request.query_params:
            data_str = request.query_params.get('data')
            try:
                from datetime import datetime
                data = datetime.strptime(data_str, '%Y-%m-%d').date()
                reservas = Reserva.objects.filter(
                    sala=obj,
                    data=data,
                    status='ativa'
                ).order_by('hora_inicio')

                horarios_bloqueados = [
                    {
                        'inicio': str(r.hora_inicio),
                        'fim': str(r.hora_fim),
                        'professor': r.professor.get_full_name() or r.professor.username
                    }
                    for r in reservas
                ]
                return {
                    'data': str(data),
                    'horarios_bloqueados': horarios_bloqueados,
                    'disponivel': len(horarios_bloqueados) == 0
                }
            except:
                return None
        return None
