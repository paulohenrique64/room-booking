#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${VENV_DIR:-.venv}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

if [[ ! -f .env ]]; then
  echo "Arquivo .env não encontrado. Crie um com as variáveis DB_* (veja README.md)."
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Criando ambiente virtual em $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Instalando dependências..."
pip install -q -r requirements.txt

export DJANGO_SETTINGS_MODULE=config.settings.development

echo "Aplicando migrações..."
python manage.py migrate --noinput

echo "Iniciando servidor em http://${HOST}:${PORT}"
python manage.py runserver "${HOST}:${PORT}"
