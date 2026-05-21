# Sistema de Agendamento de Salas

Backend Django com interface **HTMX + Bootstrap** e API REST opcional (JWT).

Parte 1 do nosso trabalho: criar o backend do sistema de agendamento de salas (modelos, regras de negocio, telas e API REST).

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

## Quick Start (Docker recomendado)

```bash
docker-compose build
docker-compose up -d
```

- **Web:** http://localhost:8080/
- **Admin:** http://localhost:8080/admin/
- **API:** http://localhost:8080/api/v1/

Para comandos do Django dentro do container:

```bash
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell
```

## Quick Start (Local)

Requer MySQL rodando no host e um `.env.local` com `DB_HOST=localhost`.

```bash
cp .env.example .env.local   # ajuste DB_* e SECRET_KEY
export $(grep -v '^#' .env.local | xargs)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
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
docker-compose config
docker-compose build
docker-compose up -d
```

Com Docker, acesse `http://localhost:8080`. O MySQL roda apenas na rede interna do compose em `db:3306`, sem publicar a porta `3306` no host. Veja mais detalhes em `DOCKER.md`.