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
./docker-manage.sh config
./docker-manage.sh build
./docker-manage.sh up-d
```

Com Docker, acesse `http://localhost:8080`. O MySQL roda apenas na rede interna do compose em `db:3306`, sem publicar a porta `3306` no host. Veja mais detalhes em `DOCKER.md`.