import os
from django.utils import timezone
from django_webtest import WebTest
from exam.decorators import fixture
from exam.cases import Exam
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User


class SmokeTest(Exam, WebTest):
    csrf_checks = False
    fixtures = ['state', 'core-test-fixtures']

    @fixture
    def user(self):
        user = User.objects.get(username="test1@example.com")
        return user

    def get(self, url):
        return self.app.get(url, user=self.user)

    def test_idea_home(self):
        page = self.get(reverse('idea:idea_list'))
        self.assertEquals(200, page.status_code)
