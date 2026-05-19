from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RecursoViewSet, SalaViewSet

router = DefaultRouter()
router.register(r'recursos', RecursoViewSet, basename='recurso')
router.register(r'salas', SalaViewSet, basename='sala')

urlpatterns = [
    path('', include(router.urls)),
]
