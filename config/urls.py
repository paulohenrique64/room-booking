"""
URL configuration principal do projeto.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def health_check(_request):
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path('health/', health_check, name='health'),
    path('', RedirectView.as_view(pattern_name='reservations:lista', permanent=False), name='home'),
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
