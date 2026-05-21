# Docker Setup - Room Booking

Este projeto roda em um unico stack Docker Compose com Django, MySQL e Nginx.

## Quick Start

```bash
docker-compose --env-file .env.docker config
docker-compose --env-file .env.docker build
docker-compose --env-file .env.docker up -d
```

A aplicacao fica disponivel em:

- Web: http://localhost:8080
- Admin: http://localhost:8080/admin/
- API: http://localhost:8080/api/v1/
- Health check: http://localhost:8080/health/

Credenciais padrao do superusuario criado no primeiro boot:

- Usuario: `admin`
- Senha: `admin123`

## Estrutura

| Servico | Funcao | Exposicao |
| --- | --- | --- |
| `db` | MySQL 8.0 | Somente rede interna Docker, `db:3306` |
| `web` | Django + Gunicorn | Somente rede interna Docker, `web:8000` |
| `nginx` | Proxy reverso e static/media | Host em `${APP_PORT:-8080}:80` |

O MySQL nao publica a porta `3306` no host. A aplicacao Django conecta no banco usando `DB_HOST=db` dentro da rede do compose.

## Variaveis

Configure `.env.docker`:

```env
APP_PORT=8080
SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,web,nginx
CSRF_TRUSTED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

DB_ENGINE=django.db.backends.mysql
DB_NAME=agendamento_salas
DB_USER=admin
DB_PASSWORD=admin
DB_HOST=db
DB_PORT=3306
MYSQL_ROOT_PASSWORD=rootadmin

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin123
```

## Comandos

```bash
docker-compose --env-file .env.docker ps
docker-compose --env-file .env.docker logs -f
docker-compose --env-file .env.docker logs -f web
docker-compose --env-file .env.docker logs -f db
docker-compose --env-file .env.docker logs -f nginx
docker-compose --env-file .env.docker exec web python manage.py shell
docker-compose --env-file .env.docker exec web python manage.py migrate
docker-compose --env-file .env.docker exec web python manage.py collectstatic --noinput --clear
```

Para recriar tudo sem preservar dados do banco:

```bash
docker-compose --env-file .env.docker down -v --remove-orphans
docker-compose --env-file .env.docker up -d
```

## Validacao Manual

```bash
docker compose --env-file .env.docker config
docker compose --env-file .env.docker ps
curl -f http://localhost:8080/health/
```

Depois confirme que apenas a porta `8080` esta publicada pelo stack, e que `3306` e `8000` nao aparecem como portas do projeto.
