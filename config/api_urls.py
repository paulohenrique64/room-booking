"""
Agregação das rotas da API v1.
"""
from django.urls import include, path

urlpatterns = [
    path('', include('apps.rooms.api.urls')),
    path('', include('apps.reservations.api.urls')),
    path('', include('apps.accounts.api.urls')),
]
