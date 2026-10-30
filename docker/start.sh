#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py import_questions   # idempotent: var olan sorulari atlar
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput || true   # kullanici varsa hata verir, yok sayilir
fi
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8080}" --workers "${WEB_CONCURRENCY:-3}" --access-logfile -
