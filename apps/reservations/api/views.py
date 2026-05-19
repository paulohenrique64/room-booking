from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.reservations import selectors, services
from apps.reservations.exceptions import DomainError
from apps.reservations.models import Reserva

from .serializers import (
    ReservaCancelSerializer,
    ReservaCreateUpdateSerializer,
    ReservaSerializer,
)


class ReservaViewSet(viewsets.ModelViewSet):
    """API REST para gerenciar reservas."""

    permission_classes = [IsAuthenticated]
    filterset_fields = ['data', 'status', 'sala']

    def get_queryset(self):
        return selectors.reservas_para_usuario(self.request.user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ReservaCreateUpdateSerializer
        return ReservaSerializer

    def perform_create(self, serializer):
        try:
            serializer.instance = services.criar_reserva(
                professor=self.request.user,
                **serializer.validated_data,
            )
        except DomainError as exc:
            raise ValidationError(exc.message) from exc

    def perform_update(self, serializer):
        try:
            serializer.instance = services.atualizar_reserva(
                reserva=self.get_object(),
                usuario=self.request.user,
                **serializer.validated_data,
            )
        except DomainError as exc:
            raise ValidationError(exc.message) from exc
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(str(exc)) from exc

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        reserva = self.get_object()
        serializer = ReservaCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            services.cancelar_reserva(
                reserva=reserva,
                usuario=request.user,
                motivo=serializer.validated_data['motivo'],
            )
        except DomainError as exc:
            return Response({'erro': exc.message}, status=status.HTTP_400_BAD_REQUEST)
        except DjangoPermissionDenied as exc:
            return Response({'erro': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response({'sucesso': 'Reserva cancelada com sucesso'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def minhas_reservas(self, request):
        reservas = selectors.reservas_para_usuario(request.user).order_by('-data', '-hora_inicio')

        status_filter = request.query_params.get('status')
        if status_filter:
            reservas = reservas.filter(status=status_filter)

        data_filter = request.query_params.get('data')
        if data_filter:
            reservas = reservas.filter(data=data_filter)

        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def proximas_reservas(self, request):
        reservas = selectors.proximas_reservas_usuario(request.user)
        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)
