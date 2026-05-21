#!/usr/bin/env bash
set -euo pipefail

HOST="${DB_HOST:-db}"
PORT="${DB_PORT:-3306}"

echo "Waiting for MySQL at $HOST:$PORT..."

python - <<'PY'
import os
import socket
import time
import sys

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "3306"))
max_retries = int(os.environ.get("DB_WAIT_RETRIES", "60"))

for i in range(max_retries):
    try:
        with socket.create_connection((host, port), timeout=2):
            pass
        print("MySQL is up!")
        sys.exit(0)
    except OSError:
        print(f"MySQL is unavailable - sleeping ({i + 1}/{max_retries})", flush=True)
        time.sleep(2)

print("Could not connect to MySQL")
sys.exit(1)
PY

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" && -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
  echo "Ensuring Django superuser exists..."
  python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ["DJANGO_SUPERUSER_USERNAME"]
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        "email": email,
        "is_staff": True,
        "is_superuser": True,
    },
)

if created:
    user.set_password(password)
    user.save(update_fields=["password"])
    print(f"Superuser '{username}' created.")
else:
    updated_fields = []
    if email and user.email != email:
        user.email = email
        updated_fields.append("email")
    if not user.is_staff:
        user.is_staff = True
        updated_fields.append("is_staff")
    if not user.is_superuser:
        user.is_superuser = True
        updated_fields.append("is_superuser")
    if updated_fields:
        user.save(update_fields=updated_fields)
    print(f"Superuser '{username}' already exists.")
PY
fi

echo "Starting Gunicorn..."
exec python -m gunicorn \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  config.wsgi:application
