from settings import *
import os

DEBUG = False

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")

SECRET_KEY = os.getenv("SECRET_KEY")


URL_PREFIX = 'feedback/'
LOGIN_URL = '/' + URL_PREFIX[:-1] + LOGIN_URL
LOGIN_REDIRECT_URL = '/' + URL_PREFIX[:-1] + LOGIN_REDIRECT_URL
ACCOUNT_LOGOUT_REDIRECT_URL = '/' + URL_PREFIX[:-1] + ACCOUNT_LOGOUT_REDIRECT_URL
SESSION_COOKIE_SECURE = True

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
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

SESSION_COOKIE_PATH = '/feedback'
SESSION_COOKIE_SECURE = True

CSRF_COOKIE_PATH = SESSION_COOKIE_PATH
CSRF_COOKIE_SECURE = True
