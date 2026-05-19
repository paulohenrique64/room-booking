from django.urls import path

from .views import MeView

urlpatterns = [
    path('usuarios/me/', MeView.as_view(), name='me'),
]
