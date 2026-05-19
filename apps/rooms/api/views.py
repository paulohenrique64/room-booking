from datetime import datetime

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.reservations import selectors

from ..models import Recurso, Sala
from .serializers import RecursoSerializer, SalaListSerializer, SalaSerializer


class RecursoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Recurso.objects.filter(ativo=True)
    serializer_class = RecursoSerializer
    permission_classes = [IsAuthenticated]


class SalaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sala.objects.filter(ativa=True)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return SalaListSerializer
        return SalaSerializer

    @action(detail=True, methods=['get'])
    def disponibilidade(self, request, pk=None):
        sala = self.get_object()
        data_str = request.query_params.get('data')

        if not data_str:
            return Response(
                {'erro': 'Parâmetro "data" é obrigatório (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'erro': 'Formato de data inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        info = selectors.disponibilidade_sala(sala, data)
        bloqueados = info['horarios_bloqueados']

        return Response({
            'sala': {
                'id': sala.id,
                'nome': sala.nome,
                'capacidade': sala.capacidade,
                'localizacao': f'{sala.predio} - Andar {sala.andar}',
            },
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
        })
