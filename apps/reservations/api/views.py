from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsOwnerOrStaff
from apps.core.utils import parse_data
from apps.reservations import selectors, services
from apps.reservations.constants import ReservaStatus
from apps.reservations.exceptions import DomainError
from apps.reservations.models import Reserva

from .serializers import (
    ReservaCancelSerializer,
    ReservaCreateUpdateSerializer,
    ReservaSerializer,
)


class ReservaViewSet(viewsets.ModelViewSet):
    """API REST para gerenciar reservas."""

    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    filterset_fields = ['data', 'status', 'sala']

    def get_queryset(self):
        return self._aplicar_filtros(selectors.reservas_para_usuario(self.request.user))

    def _aplicar_filtros(self, queryset):
        status_filter = self.request.query_params.get('status')
        if status_filter:
            status_validos = {choice[0] for choice in ReservaStatus.choices}
            if status_filter not in status_validos:
                raise ValidationError({'status': 'Status inválido.'})
            queryset = queryset.filter(status=status_filter)

        data_filter = self.request.query_params.get('data')
        if data_filter:
            try:
                data = parse_data(data_filter)
            except DjangoValidationError as exc:
                raise ValidationError({'data': exc.messages}) from exc
            queryset = queryset.filter(data=data)

        sala_filter = self.request.query_params.get('sala')
        if sala_filter:
            if not sala_filter.isdigit():
                raise ValidationError({'sala': 'Sala inválida.'})
            queryset = queryset.filter(sala_id=sala_filter)

        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ReservaCreateUpdateSerializer
        return ReservaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            self._serialize_reserva(serializer.instance).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(self._serialize_reserva(serializer.instance).data)

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

    def _serialize_reserva(self, reserva):
        return ReservaSerializer(reserva, context=self.get_serializer_context())

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

        reserva.refresh_from_db()
        return Response(self._serialize_reserva(reserva).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def minhas_reservas(self, request):
        reservas = self.get_queryset().order_by('-data', '-hora_inicio')

        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def proximas_reservas(self, request):
        reservas = selectors.proximas_reservas_usuario(request.user)
        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)
