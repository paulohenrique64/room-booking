from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Sala, Reserva, CancelamentoReserva, HistoricoReserva, Recurso
from .serializers import (
    SalaSerializer, SalaListSerializer, ReservaSerializer,
    ReservaCreateUpdateSerializer, ReservaCancelSerializer,
    RecursoSerializer, UserSerializer
)


class RecursoViewSet(viewsets.ReadOnlyModelViewSet):
    """API para listar recursos disponíveis"""
    queryset = Recurso.objects.filter(ativo=True)
    serializer_class = RecursoSerializer
    permission_classes = [IsAuthenticated]


class SalaViewSet(viewsets.ReadOnlyModelViewSet):
    """API para listar salas com filtros de disponibilidade"""
    queryset = Sala.objects.filter(ativa=True)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return SalaListSerializer
        return SalaSerializer

    @action(detail=True, methods=['get'])
    def disponibilidade(self, request, pk=None):
        """
        Retorna horários disponíveis para uma sala em uma data específica
        Query params: data (YYYY-MM-DD), hora_inicio, hora_fim
        """
        sala = self.get_object()
        data_str = request.query_params.get('data')

        if not data_str:
            return Response(
                {'erro': 'Parâmetro "data" é obrigatório (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from datetime import datetime
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'erro': 'Formato de data inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reservas ativas nesta sala e data
        reservas = Reserva.objects.filter(
            sala=sala,
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

        return Response({
            'sala': {
                'id': sala.id,
                'nome': sala.nome,
                'capacidade': sala.capacidade,
                'localizacao': f'{sala.predio} - Andar {sala.andar}'
            },
            'data': str(data),
            'horarios_bloqueados': horarios_bloqueados,
            'disponivel': len(horarios_bloqueados) == 0
        })


class ReservaViewSet(viewsets.ModelViewSet):
    """API para gerenciar reservas"""
    permission_classes = [IsAuthenticated]
    filterset_fields = ['data', 'status', 'sala']

    def get_queryset(self):
        user = self.request.user
        # Admins veem tudo, usuários comuns veem apenas suas reservas
        if user.is_staff:
            return Reserva.objects.all()
        return Reserva.objects.filter(professor=user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ReservaCreateUpdateSerializer
        return ReservaSerializer

    def perform_create(self, serializer):
        """Criar nova reserva sempre com o usuário atual como professor"""
        reserva = serializer.save(professor=self.request.user)
        # Registrar no histórico
        HistoricoReserva.objects.create(
            reserva=reserva,
            acao='criada',
            usuario=self.request.user,
            descricao='Reserva criada pelo usuário'
        )

    def perform_update(self, serializer):
        """Atualizar reserva (apenas professores comuns podem editar suas próprias reservas)"""
        user = self.request.user
        reserva = self.get_object()

        # Verificar permissão
        if not user.is_staff and reserva.professor != user:
            raise PermissionError('Você só pode editar suas próprias reservas.')

        # Não permitir editar reservas canceladas ou finalizadas
        if reserva.status != 'ativa':
            raise PermissionError('Não é possível editar uma reserva cancelada ou finalizada.')

        serializer.save()
        # Registrar no histórico
        HistoricoReserva.objects.create(
            reserva=reserva,
            acao='editada',
            usuario=user,
            descricao='Reserva editada'
        )

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancelar uma reserva"""
        reserva = self.get_object()
        user = request.user

        # Verificar permissão
        if not user.is_staff and reserva.professor != user:
            return Response(
                {'erro': 'Você só pode cancelar suas próprias reservas'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verificar se já foi cancelada
        if reserva.status == 'cancelada':
            return Response(
                {'erro': 'Esta reserva já foi cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar dados
        serializer = ReservaCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Cancelar reserva
        reserva.status = 'cancelada'
        reserva.save()

        # Registrar cancelamento
        CancelamentoReserva.objects.create(
            reserva=reserva,
            motivo=serializer.validated_data['motivo'],
            cancelado_por=user
        )

        # Registrar no histórico
        HistoricoReserva.objects.create(
            reserva=reserva,
            acao='cancelada',
            usuario=user,
            descricao=f'Reserva cancelada: {serializer.validated_data["motivo"]}'
        )

        return Response(
            {'sucesso': 'Reserva cancelada com sucesso'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def minhas_reservas(self, request):
        """Listar todas as reservas do usuário autenticado"""
        user = request.user
        reservas = Reserva.objects.filter(professor=user).order_by('-data', '-hora_inicio')

        # Filtrar por status se fornecido
        status_filter = request.query_params.get('status')
        if status_filter:
            reservas = reservas.filter(status=status_filter)

        # Filtrar por data se fornecido
        data_filter = request.query_params.get('data')
        if data_filter:
            reservas = reservas.filter(data=data_filter)

        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def proximas_reservas(self, request):
        """Listar próximas reservas do usuário (próximos 30 dias)"""
        from datetime import timedelta
        user = request.user
        hoje = timezone.now().date()
        data_limite = hoje + timedelta(days=30)

        reservas = Reserva.objects.filter(
            professor=user,
            data__gte=hoje,
            data__lte=data_limite,
            status='ativa'
        ).order_by('data', 'hora_inicio')

        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)

