"""
URL configuration principal do projeto.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView
from apps.core import views as core_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def health_check(_request):
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path('health/', health_check, name='health'),
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='home'),
    path('dashboard/', core_views.DashboardView.as_view(), name='dashboard'),
    path('notificacoes/dispensar/', core_views.notification_dismiss, name='notification_dismiss'),
    path('equipamentos/', core_views.EquipmentListView.as_view(), name='equipment'),
    path('equipamentos/novo/', core_views.equipamento_modal, name='equipment_new'),
    path('equipamentos/<int:pk>/editar/', core_views.equipamento_modal, name='equipment_edit'),
    path('equipamentos/<int:pk>/excluir/', core_views.equipamento_delete, name='equipment_delete'),
    path('salas/novo/', core_views.sala_modal, name='room_new'),
    path('salas/<int:pk>/editar/', core_views.sala_modal, name='room_edit'),
    path('salas/<int:pk>/excluir/', core_views.sala_delete, name='room_delete'),
    path('relatorios/', core_views.ReportsView.as_view(), name='reports'),
    path('admin/', admin.site.urls),
    # Autenticação web
    path('contas/', include('apps.accounts.urls')),
    # Interface HTMX
    path('salas/', include('apps.rooms.urls')),
    path('reservas/', include('apps.reservations.urls')),
    # API REST (JWT)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/', include('config.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
