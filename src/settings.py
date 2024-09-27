# coding=utf-8
# Django settings for feedback project.

# determine if this is a production system
import os
import sys
from django.utils.translation import pgettext_lazy as _

DEBUG = True

ADMINS = (
    ('Feedback-Team', 'feedback@lists.d120.de'),
)

MANAGERS = ADMINS
EMAIL_SUBJECT_PREFIX = ''

BASE_PATH = os.path.dirname(os.path.abspath(__file__)) + '/../'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_PATH + "db/feedback.db",
        'USER': '',
        'PASSWORD': '',
    }
}

ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Berlin'

USE_TZ = False # before django 5.0 USE_TZ was default False

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'de-DE'

LANGUAGES = [
    ("de", _("German")),
    ("en", _("English")),
]

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = BASE_PATH + 'static/'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/feedback/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    BASE_PATH + 'media/',
    BASE_PATH + 'node_modules/',
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 's=15!5%-sw+4w*hsw(=h%rzyn&jy*&l1w%x2z4$5d^4p&feiwb'

# Testing Setting to unload the debug toolbar when testing, see https://github.com/jazzband/django-debug-toolbar/issues/1405
TESTING = 'test' or 'check' in sys.argv

# List of callables that know how to import templates from various sources.
# Filesystem muss vor app_directories stehen, damit unsere Templates für registration den Standard
# überschreiben!

MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'feedback.auth.FSDebugRemoteUserMiddleware',
]
if not TESTING:
    MIDDLEWARE += 'debug_toolbar.middleware.DebugToolbarMiddleware'

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_PATH + "src/templates"],
        'OPTIONS': {
            'context_processors': ['django.contrib.auth.context_processors.auth',
            "django.contrib.messages.context_processors.messages",
            "django.template.context_processors.request",
            ],
            'loaders': [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
            ]
        },
    },
]


INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes', # wird von admin benötigt
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.messages',
    'formtools',
    'feedback',
]

if not TESTING:
    INSTALLED_APPS += 'django_debug'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'feedback.auth.FSAccountBackend',
    'feedback.auth.TakeoverBackend',
    'feedback.auth.VeranstalterBackend',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}

LOGIN_URL = '/intern/'
LOGIN_REDIRECT_URL = '/intern/uebersicht/'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Common Middleware settings
APPEND_SLASH = True

# Path to LaTeX files
LATEX_PATH = BASE_PATH + 'latex/anschreiben/'

TESTDATA_PATH = BASE_PATH + 'testdata/'

# Ranking
THRESH_SHOW = 5
THRESH_VALID = 20

DEFAULT_FROM_EMAIL = "Feedback-Team <feedback@fachschaft.informatik.tu-darmstadt.de>"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

USERNAME_VERANSTALTER = 'veranstalter'

# for debug toolbar
INTERNAL_IPS = ('127.0.0.1',)

# Coverage testing
#TEST_RUNNER = 'django_coverage.coverage_runner.CoverageRunner'
COVERAGE_REPORT_HTML_OUTPUT_DIR = BASE_PATH + 'htmlcov'
COVERAGE_PATH_EXCLUDES = [r'.svn', r'templates']
COVERAGE_MODULE_EXCLUDES = ['tests$', 'settings$', 'locale$', 'django', 'migrations', 'south',
                            'debug_toolbar']
COVERAGE_CODE_EXCLUDES = ['from .* import .*', 'import .*']

DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS': False}

# application-specific-cookies
CSRF_COOKIE_NAME = 'pyfeedback_csrftoken'
SESSION_COOKIE_NAME = 'pyfeedback_sessionid'
