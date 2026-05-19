from django.urls import path

from . import views

app_name = 'reservations'

urlpatterns = [
    path('', views.ReservaListView.as_view(), name='lista'),
    path('nova/', views.ReservaCreateView.as_view(), name='nova'),
    path('<int:pk>/cancelar/', views.ReservaCancelarView.as_view(), name='cancelar'),
]
