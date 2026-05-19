"""
WSGI config for agendamento_salas project.
"""
import os

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
