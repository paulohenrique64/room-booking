"""
ASGI config for agendamento_salas project.
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

from django.core.asgi import get_asgi_application  # noqa: E402

application = get_asgi_application()
