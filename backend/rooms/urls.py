from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalaViewSet, ReservaViewSet, RecursoViewSet

router = DefaultRouter()
router.register(r'recursos', RecursoViewSet, basename='recurso')
router.register(r'salas', SalaViewSet, basename='sala')
router.register(r'reservas', ReservaViewSet, basename='reserva')

app_name = 'rooms'

urlpatterns = [
    path('', include(router.urls)),
]
