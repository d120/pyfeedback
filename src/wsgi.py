import os

from django.core.wsgi import get_wsgi_application

# select in .env which settings to use
settings_file = os.getenv("SETTINGS_FILE", "settings")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_file)

application = get_wsgi_application()
