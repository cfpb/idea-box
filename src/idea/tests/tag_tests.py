from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
from django.utils import unittest
from django.test.client import RequestFactory
from idea import models, views
from idea.tests.utils import random_user, login, create_superuser
if 'core.taggit' in settings.INSTALLED_APPS:
    from core.taggit.utils import add_tags
    COLLAB_TAGS = True;
else:
    COLLAB_TAGS = False;

class TagTest(TestCase):
    fixtures = ['state']

    def setUp(self):
        create_superuser()

    @unittest.skipIf(COLLAB_TAGS == False, "Remove only works with collab's core.taggit")
    def test_tag_remove_exists_for_creator(self):
        """
        Detail page allows for removal of tags created by the current user
        """
        user1 = login(self)
        idea = models.Idea(creator=user1, title='AAAA', 
                state = models.State.objects.get(name='Active'))
        idea.save()
        add_tags(idea, 'AAA', None, user1, 'idea')

        response = self.client.get(reverse("idea:idea_detail", args=(str(idea.id),)))
        self.assertContains(response, 'aaa')
        self.assertContains(response, 'tag_remove')

    @unittest.skipIf(COLLAB_TAGS == False, "Remove only works with collab's core.taggit")
    def test_tag_remove_not_exists_for_random_user(self):
        """
        Detail page does not allow for removal of tags created by a different user
        """
        login(self)
        user1 = random_user()
        idea = models.Idea(creator=user1, title='AAAA', 
                state = models.State.objects.get(name='Active'))
        idea.save()
        add_tags(idea, 'AAA', None, user1, 'idea')

        response = self.client.get(reverse("idea:idea_detail", args=(str(idea.id),)))
        self.assertContains(response, 'aaa')
        self.assertNotContains(response, 'tag_remove')

    @unittest.skipIf(COLLAB_TAGS == False, "Remove only works with collab's core.taggit")
    def test_tag_remove_not_exists_for_different_idea(self):
        """
        Detail page does not allow for removal of tags created by a different user
        """
        user1 = login(self)
        user2 = random_user()
        idea = models.Idea(creator=user1, title='AAAA', 
                state = models.State.objects.get(name='Active'))
        idea.save()
        idea2 = models.Idea(creator=user2, title='BBBB', 
                state = models.State.objects.get(name='Active'))
        idea2.save()
        add_tags(idea, 'AAA', None, user1, 'idea')
        add_tags(idea2, 'AAA', None, user2, 'idea')

        response = self.client.get(reverse("idea:idea_detail", args=(str(idea2.id),)))
        self.assertContains(response, 'aaa')
        self.assertNotContains(response, 'tag_remove')

    @unittest.skipIf(COLLAB_TAGS == False, "Remove only works with collab's core.taggit")
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

