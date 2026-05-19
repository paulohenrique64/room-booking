# Sistema de Agendamento de Salas

Backend Django com interface **HTMX + Bootstrap** e API REST opcional (JWT).

## Estrutura

```
├── apps/
│   ├── core/           # mixins e utilitários
│   ├── accounts/       # login, sessão
│   ├── rooms/          # salas e recursos
│   │   └── api/        # endpoints REST
│   └── reservations/   # reservas
│       ├── services.py # regras de negócio
│       ├── selectors.py
│       └── api/
├── config/settings/    # base, development, production
├── templates/          # layout global
└── static/
```

## Quick Start

```bash
cp .env.example .env   # ajuste DB_* e SECRET_KEY
./run.sh
```

- **Reservas (web):** http://localhost:8000/reservas/
- **Salas:** http://localhost:8000/salas/
- **Login:** http://localhost:8000/contas/login/
- **Admin:** http://localhost:8000/admin/
- **API:** http://localhost:8000/api/v1/

## Stack

- Django 4.2 + django-htmx
- Bootstrap 5 (CDN)
- DRF + SimpleJWT (API)
- MySQL (PyMySQL)

## Docker

```bash
docker compose up --build
```

## Camadas

| Camada | Onde |
|--------|------|
| Domínio | `models.py`, `services.py` |
| Consultas | `selectors.py` |
| Web HTMX | `views.py`, `forms.py`, `templates/` |
| API | `api/views.py`, `api/serializers.py` |
