#!/bin/bash
set -e

if [ "$1" = 'supervisord' ]; then
    chown -R celery:celery /var/lib/celery
    /var/venv/bin/python /app/manage.py migrate --noinput
    /var/venv/bin/python /app/manage.py collectstatic --noinput
    exec "$@"
fi

exec "$@"
