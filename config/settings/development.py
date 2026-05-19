"""
Configurações de desenvolvimento.
"""
import os

# Fallback apenas para ambiente local de desenvolvimento
os.environ.setdefault('SECRET_KEY', 'django-insecure-dev-only-change-in-production')

from .base import *  # noqa: F401, F403

DEBUG = True
