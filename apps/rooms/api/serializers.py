from rest_framework import serializers

from apps.core.utils import parse_data
from apps.reservations import selectors

from ..models import Recurso, Sala


class RecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recurso
        fields = ['id', 'nome', 'descricao', 'ativo']


class SalaSerializer(serializers.ModelSerializer):
    recursos = RecursoSerializer(many=True, read_only=True)
    localizacao = serializers.SerializerMethodField()

    class Meta:
        model = Sala
        fields = [
            'id', 'nome', 'predio', 'andar', 'capacidade',
            'descricao', 'recursos', 'ativa', 'localizacao',
        ]

    def get_localizacao(self, obj):
        return f'{obj.predio} - Andar {obj.andar}'


class SalaListSerializer(serializers.ModelSerializer):
    """
    Serializer otimizado para listagem de salas.
    
    Usa annotate no queryset para evitar N+1 query ao calcular disponibilidade.
    """
    recursos = RecursoSerializer(many=True, read_only=True)
    disponibilidade = serializers.SerializerMethodField()

    class Meta:
        model = Sala
        fields = ['id', 'nome', 'predio', 'andar', 'capacidade', 'recursos', 'disponibilidade']

    def get_disponibilidade(self, obj):
        request = self.context.get('request')
        if not request or 'data' not in request.query_params:
            return None

        data_str = request.query_params.get('data')
        try:
            data = parse_data(data_str)
        except Exception:
            return None

        info = selectors.disponibilidade_sala(obj, data)
        bloqueados = info['horarios_bloqueados']
        return {
            'data': str(data),
            'horarios_bloqueados': [
                {
                    'inicio': b['inicio_str'],
                    'fim': b['fim_str'],
                    'professor': b['professor'],
                }
                for b in bloqueados
            ],
            'disponivel': info['disponivel'],
        }
