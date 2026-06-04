from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('perfil/', views.ProfileView.as_view(), name='profile'),
    path('acessos/', views.AccessManagementView.as_view(), name='access'),
    path('usuarios/novo/', views.user_modal, name='user_new'),
    path('usuarios/<int:pk>/editar/', views.user_modal, name='user_edit'),
    path('usuarios/<int:pk>/excluir/', views.user_delete, name='user_delete'),
    path('grupos/novo/', views.group_modal, name='group_new'),
    path('grupos/<int:pk>/editar/', views.group_modal, name='group_edit'),
    path('grupos/<int:pk>/excluir/', views.group_delete, name='group_delete'),
]
