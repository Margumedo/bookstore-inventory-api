#!/bin/sh
set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput
python manage.py createcachetable

echo "Recolectando archivos estaticos..."
python manage.py collectstatic --noinput

PORT="${PORT:-8000}"
WORKERS="${WEB_CONCURRENCY:-2}"

echo "Iniciando gunicorn en 0.0.0.0:${PORT}..."
exec gunicorn bookstore.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers "${WORKERS}" \
    --timeout 120
