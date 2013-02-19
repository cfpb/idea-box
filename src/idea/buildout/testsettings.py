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

INSTALLED_APPS = ['idea', 
    'south',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'taggit',
    'haystack',
    'django.contrib.comments',
    'django.contrib.staticfiles',
]

ROOT_URLCONF = 'idea.buildout.urls'

HAYSTACK_SITECONF = 'idea.buildout.search_sites'
HAYSTACK_SEARCH_ENGINE = 'simple'

DEBUG = True
STATIC_URL = '/static/'
