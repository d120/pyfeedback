#!/bin/sh

# Exit on error
set -e

echo "Applying database migrations..."
python manage.py migrate --no-input

if [ $# -eq 0 ]; then

    if [ "$DJANGO_SETTINGS_MODULE" = "settings.dev" ]; then
        echo "Starting Django development server..."
        exec python manage.py runserver 0.0.0.0:8000

    elif [ "$DJANGO_SETTINGS_MODULE" = "settings.prod" ]; then
        echo "Starting Gunicorn with ${GUNICORN_WORKERS:-3} workers..."
        exec gunicorn \
            --bind 0.0.0.0:8000 \
            --workers "${GUNICORN_WORKERS:-3}" \
            wsgi:application

    else
        echo "Unknown DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
        exit 1
    fi

else
    echo "Running custom command: $@"
    exec "$@"
fi
