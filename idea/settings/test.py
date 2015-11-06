from .base import *

INSTALLED_APPS += ('django_nose',)
TEST_RUNNER = 'django_nose.runner.NoseTestSuiteRunner'
