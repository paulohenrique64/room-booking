from django.urls import path

from . import views

app_name = 'rooms'

urlpatterns = [
    path('', views.SalaListView.as_view(), name='lista'),
    path('<int:pk>/', views.SalaDetailView.as_view(), name='detalhe'),
]
