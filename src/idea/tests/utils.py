from django.contrib.auth.models import User
from django.test.client import RequestFactory
import random
import string

def random_user():
    return User.objects.create_user(
            ''.join(random.choice(string.lowercase) for _ in range(12)))


def mock_req(path='/', user = None):
    """
    Mock request -- with user!
    """
    if not user:
        user = random_user()
    req = RequestFactory().get(path)
    req.user = user
    return req

