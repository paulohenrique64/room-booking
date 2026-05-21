"""
Configurações para execução local via Docker Compose.
"""
import os

os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,web,nginx")
os.environ.setdefault("CSRF_TRUSTED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080")
os.environ.setdefault("DB_HOST", "db")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_USER", "admin")

from .base import *  # noqa: F401, F403

DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# O compose local roda em HTTP atrás do Nginx.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
