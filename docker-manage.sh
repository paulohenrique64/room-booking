#!/usr/bin/env bash
set -euo pipefail

COMMAND=${1:-help}
ENV_FILE=${ENV_FILE:-.env.docker}

compose() {
    docker compose --env-file "$ENV_FILE" "$@"
}

app_port() {
    awk -F= '$1 == "APP_PORT" { print $2; found = 1 } END { if (!found) print "8080" }' "$ENV_FILE" 2>/dev/null
}

show_help() {
    echo "Room Booking - Docker Management Script"
    echo ""
    echo "Usage: ./docker-manage.sh [command]"
    echo "Env file: $ENV_FILE"
    echo ""
    echo "Commands:"
    echo "  config      - Validate and render compose configuration"
    echo "  build       - Build Docker images"
    echo "  up          - Start containers in foreground"
    echo "  up-d        - Start containers in background (detached)"
    echo "  down        - Stop and remove containers"
    echo "  ps          - Show container status"
    echo "  logs        - Show logs from all containers"
    echo "  logs-web    - Show logs from web container only"
    echo "  logs-db     - Show logs from database container only"
    echo "  logs-nginx  - Show logs from nginx container only"
    echo "  shell       - Open Django shell in web container"
    echo "  migrate     - Run database migrations"
    echo "  createsuperuser - Create superuser interactively"
    echo "  collectstatic - Collect static files"
    echo "  test        - Run Django test suite"
    echo "  clean       - Remove containers, volumes and images"
    echo "  help        - Show this help message"
    echo ""
}

case $COMMAND in
    config)
        echo "Validating Docker Compose config..."
        compose config
        ;;
    build)
        echo "Building Docker images..."
        compose build
        ;;
    up)
        echo "Starting containers..."
        compose up
        ;;
    up-d)
        echo "Starting containers in background..."
        compose up -d
        echo "Containers started. Run './docker-manage.sh logs' to see logs"
        echo "Application available at http://localhost:$(app_port)"
        ;;
    down)
        echo "Stopping containers..."
        compose down
        ;;
    ps)
        echo "Showing container status..."
        compose ps
        ;;
    logs)
        echo "Showing logs from all containers..."
        compose logs -f
        ;;
    logs-web)
        echo "Showing logs from web container..."
        compose logs -f web
        ;;
    logs-db)
        echo "Showing logs from database container..."
        compose logs -f db
        ;;
    logs-nginx)
        echo "Showing logs from nginx container..."
        compose logs -f nginx
        ;;
    shell)
        echo "Opening Django shell..."
        compose exec web python manage.py shell
        ;;
    migrate)
        echo "Running migrations..."
        compose exec web python manage.py migrate
        ;;
    createsuperuser)
        echo "Creating superuser..."
        compose exec web python manage.py createsuperuser
        ;;
    collectstatic)
        echo "Collecting static files..."
        compose exec web python manage.py collectstatic --noinput --clear
        ;;
    test)
        echo "Running Django tests..."
        compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web python manage.py test
        ;;
    clean)
        echo "Cleaning up Docker resources..."
        compose down -v --remove-orphans
        echo "Cleanup complete"
        ;;
    *)
        show_help
        ;;
esac
