from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import unittest
from django.test.client import RequestFactory
from idea import models, views
from idea.tests.utils import mock_req, random_user
try:
    from core.taggit.utils import add_tags
    from core.taggit.models import TaggedItem
    ADD_TAGS = True;
except ImportError:
    from taggit.models import TaggedItem
    ADD_TAGS = False;

class TagTest(TestCase):
    fixtures = ['state', 'core-test-fixtures']

    @unittest.skipIf(ADD_TAGS == False, "Remove only works with collab's core.taggit")
    def test_tag_remove_exists_for_creator(self):
        """
        Detail page allows for removal of tags created by the current user
        """
        self.client.login(username='test1@example.com', password='1')
        user1 = User.objects.get(username='test1@example.com')
        idea = models.Idea(creator=user1, title='AAAA', 
                state = models.State.objects.get(name='Active'))
        idea.save()
        add_tags(idea, 'AAA', None, user1, 'idea')

        response = self.client.get(reverse("idea:idea_detail", args=(str(idea.id),)))
        self.assertContains(response, 'aaa')
        self.assertContains(response, 'tag_remove')

    @unittest.skipIf(ADD_TAGS == False, "Remove only works with collab's core.taggit")
    def test_tag_remove_not_exists_for_random_user(self):
        """
        Detail page does not allow for removal of tags created by a different user
        """
        self.client.login(username='test1@example.com', password='1')
        user1 = random_user()
        idea = models.Idea(creator=user1, title='AAAA', 
                state = models.State.objects.get(name='Active'))
        idea.save()
        add_tags(idea, 'AAA', None, user1, 'idea')

        response = self.client.get(reverse("idea:idea_detail", args=(str(idea.id),)))
        self.assertContains(response, 'aaa')
        self.assertNotContains(response, 'tag_remove')

    @unittest.skipIf(ADD_TAGS == False, "Remove only works with collab's core.taggit")
    def test_tag_remove(self):
        """
        Detail page tag form submission should add tags.
        """
        user1 = random_user()
        idea = models.Idea(creator=user1, title='AAAA', 
                state = models.State.objects.get(name='Active'))
        idea.save()
        add_tags(idea, 'AAA', None, user1, 'idea')

        # Attempting to remove as a different user fails
        req = RequestFactory().post('/', {})
        req.user = random_user()
        response = views.remove_tag(req, str(idea.id), 'aaa')
        self.assertEqual(response.status_code, 302)
        self.assertIn('aaa', set([tag.slug for tag in idea.tags.all()]))

        # Attempting to remove as the creator succeeds
        req.user = user1
        response = views.remove_tag(req, str(idea.id), 'aaa')
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('aaa', set([tag.slug for tag in idea.tags.all()]))

