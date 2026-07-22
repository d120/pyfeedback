#!/bin/sh

# Exit on error
set -e

echo "Applying database migrations..."
python manage.py migrate --no-input

if [ $# -eq 0 ]; then
    echo "Starting Gunicorn with ${GUNICORN_WORKERS:-3} workers..."
    exec gunicorn --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-3}" wsgi:application
else
    # (bash, python manage.py createsuperuser etc.)
    echo "Running custom command: $@"
    exec "$@"
fi
