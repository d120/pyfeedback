from settings import *
import settings_secret as secrets

DEBUG = False

ALLOWED_HOSTS = ['.fachschaft.informatik.tu-darmstadt.de', '.d120.de']

SECRET_KEY = secrets.SECRET_KEY


URL_PREFIX = 'feedback/'
LOGIN_URL = '/' + URL_PREFIX[:-1] + LOGIN_URL
LOGIN_REDIRECT_URL = '/' + URL_PREFIX[:-1] + LOGIN_REDIRECT_URL
SESSION_COOKIE_SECURE = True

# @see https://docs.djangoproject.com/es/1.9/topics/email/
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'mail.d120.de'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'pyfeedback'
EMAIL_HOST_PASSWORD = secrets.EMAIL_HOST_PASSWORD

SESSION_COOKIE_PATH = '/feedback'
SESSION_COOKIE_SECURE = True

CSRF_COOKIE_PATH = SESSION_COOKIE_PATH
CSRF_COOKIE_SECURE = True
