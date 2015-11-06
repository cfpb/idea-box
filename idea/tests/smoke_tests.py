import os
from django.utils import timezone
from django_webtest import WebTest
from exam.decorators import fixture
from exam.cases import Exam
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from idea.tests.utils import get_login_user, create_superuser


class SmokeTest(Exam, WebTest):
    csrf_checks = False
    fixtures = ['state']

    def setUp(self):
        create_superuser()

    @fixture
    def user(self):
        user = get_login_user()
        return user

    def get(self, url):
        return self.app.get(url, user=self.user)

    def test_idea_home(self):
        page = self.get(reverse('idea:idea_list'))
        self.assertEquals(200, page.status_code)
