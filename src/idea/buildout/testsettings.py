import logging
import south.logger
# Stop South from spitting out debug messages during tests
logging.getLogger('south').setLevel(logging.CRITICAL)

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'ideatest',
            'USER': 'root',
            'PASSWORD': '',
            'HOST': '',  # Set to empty string for localhost
            'PORT': '',  # Set to empty string for default
        },
}

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

SITE_ID = 1

TEMPLATE_DIRS = (
    './templates',
)

INSTALLED_APPS = [
    'idea', 
    'south',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'haystack',
    'django_nose',
    'django.contrib.comments',
    'django.contrib.staticfiles',
    'mptt',
    'core', # collab core
    'core.taggit',
]

ROOT_URLCONF = 'idea.buildout.urls'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

DEBUG = True
STATIC_URL = '/static/'

# Only used in tests
SECRET_KEY = '-9khc0wuc!ie88^tsqx9fiq!utst+d!!o@n+jqxz97s)ek74_@'

TEST_RUNNER = 'django_nose.runner.NoseTestSuiteRunner'

AUTH_USER_MODEL = 'core.CollabUser'
