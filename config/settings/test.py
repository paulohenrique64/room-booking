"""
Configuracoes para a suite automatizada de testes.
"""
import os

os.environ.setdefault('SECRET_KEY', 'django-insecure-test-only')
os.environ.setdefault('DEBUG', 'False')
os.environ.setdefault('ALLOWED_HOSTS', 'testserver,localhost,127.0.0.1')
os.environ.setdefault('CSRF_TRUSTED_ORIGINS', 'http://testserver,http://localhost:8080')

from .base import *  # noqa: F401, F403

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
