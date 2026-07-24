import os
from .base import *

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    host.strip() for host in os.getenv("ALLOWED_HOSTS", "").split(",") if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()
]

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY and not DEBUG:
    raise ValueError("CRITICAL: SECRET_KEY environment variable is missing!")


URL_PREFIX = 'feedback/'
LOGIN_URL = '/' + URL_PREFIX[:-1] + LOGIN_URL
LOGIN_REDIRECT_URL = '/' + URL_PREFIX[:-1] + LOGIN_REDIRECT_URL
ACCOUNT_LOGOUT_REDIRECT_URL = '/' + URL_PREFIX[:-1] + ACCOUNT_LOGOUT_REDIRECT_URL

SESSION_COOKIE_PATH = '/feedback'
SESSION_COOKIE_SECURE = True

CSRF_COOKIE_PATH = SESSION_COOKIE_PATH
CSRF_COOKIE_SECURE = True

SOCIALACCOUNT_PROVIDERS = {
    "openid_connect": {
        "APPS": [
            {
                "provider_id": "keycloak",
                "name": "Keycloak",
                "client_id": os.getenv("KEYCLOAK_CLIENT_ID"),
                "secret": os.getenv("KEYCLOAK_SECRET"),
                "settings": {
                    "server_url": os.getenv("KEYCLOAK_SERVER_URL"),
                },
            }
        ]
    }
}

# @see https://docs.djangoproject.com/es/1.9/topics/email/
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv("EMAIL_HOST")

email_port_env = os.getenv("EMAIL_PORT", "").strip()
EMAIL_PORT = int(email_port_env) if email_port_env else 587

EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")