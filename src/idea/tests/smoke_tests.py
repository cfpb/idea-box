import os
from django.utils import timezone
from django_webtest import WebTest
from exam.decorators import fixture
from exam.cases import Exam
from django.core.urlresolvers import reverse


class SmokeTest(Exam, WebTest):
    csrf_checks = False
    fixtures = ['state']

    @fixture
    def user(self):
        try:
            from collab.django_factories import UserF
            return UserF(username="test1@example.com", person__title='')
        except ImportError:
            from django.contrib.auth.models import User
            user = User()
            user.username = "test1@example.com"
            user.first_name = 'first'
            user.last_name = 'last'
            user.email = '"test1@example.com"'
            user.password = 'pbkdf2_sha256$10000$ggAKkiHobFL8$xQzwPeHNX1vWr9uNmZ/gKbd17uLGZVM8QNcgmaIEAUs='
            user.is_staff = False
            user.is_active = True
            user.is_superuser = False
            user.last_login = timezone.now()
            user.date_joined = timezone.now()
            user.save()
            return user

    def get(self, url):
        return self.app.get(url, user=self.user)

    def test_idea_home(self):
        page = self.get(reverse('idea:idea_list'))
        self.assertEquals(200, page.status_code)
