#!/bin/sh

# Exit on error
set -e

echo "Applying database migrations..."
python manage.py migrate --no-input

# Start the application
echo "Starting Gunicorn..."
exec "$@"