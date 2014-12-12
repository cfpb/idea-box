from django.contrib.auth import get_user_model
from django.test.client import RequestFactory
from django.conf import settings
import random
import string

def random_user():
    username = ''.join(random.choice(string.lowercase) for _ in range(12))
    return get_user_model().objects.create_user(
        username=username, email="%s@example.com" % username,
        first_name=username)

def create_superuser():
    user = get_user_model().objects.create_superuser('test1@example.com', 'test1@example.com', '1')
    # If using collab, person objects needs to be created too
    if 'core' in settings.INSTALLED_APPS:
        from core.models import Person
        person = Person()
        person.user = user
        person.save()

def get_login_user():
    # required for Collab integration
    if get_user_model().objects.filter(username='test1@example.com').exists():
        return get_user_model().objects.get(username='test1@example.com')
    else:
        user = random_user()
        return user

def login(testcase):
    user = get_login_user()
    # required for Collab integration
    if user.username == 'test1@example.com':
        testcase.client.login(username='test1@example.com', password='1')
    else:
        testcase.client.login(username=user.username)
    return user

def mock_req(path='/', user = None):
    """
    Mock request -- with user!
    """
    if not user:
        user = random_user()
    req = RequestFactory().get(path)
    req.user = user
    return req

