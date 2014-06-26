from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import unittest
from haystack import connections
from idea import models, views
from idea.tests.utils import mock_req, random_user
from mock import patch
from datetime import date, timedelta
from idea.forms import IdeaForm

try:
    from core.taggit.utils import add_tags
    from core.taggit.models import TaggedItem
    COLLAB_TAGS = True;
except ImportError:
    COLLAB_TAGS = False;

class AddIdeaTest(TestCase):
    fixtures = ['state', 'core-test-fixtures']

    def test_good_idea(self):
        """ Test an normal POST submission to add an idea. """

        self.client.login(username='test1@example.com', password='1')
        self.assertEquals(models.Idea.objects.all().count(), 0)
        num_voters = get_user_model().objects.filter(vote__idea__pk=1, vote__vote=1).count()
        self.assertEqual(num_voters, 0)
        resp = self.client.post(reverse('idea:add_idea'), {'title':'test title', 'summary':'test summary', 'text':'test text', 'tags':'test, tags'})
        self.assertContains(resp, 'Thanks for sharing your Idea')
        self.assertEquals(models.Idea.objects.all().count(), 1)

        num_voters = get_user_model().objects.filter(vote__idea__pk=1, vote__vote=1).count()
        self.assertEqual(num_voters, 1)

    def test_duplicate_idea(self):
        """ Test an duplicate POST submission to add an idea. """
        self.client.login(username='test1@example.com', password='1')
        self.assertEquals(models.Idea.objects.all().count(), 0)
        resp = self.client.post(reverse('idea:add_idea'), {'title':'test title', 'summary':'test summary', 'text':'test text', 'tags':'test, tags'})
        self.assertEquals(models.Idea.objects.all().count(), 1)
        resp = self.client.post(reverse('idea:add_idea'), {'title':'test title', 'summary':'new summary', 'text':'new text', 'tags':'new, tags'})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('detail', resp['Location'])
        self.assertEquals(models.Idea.objects.all().count(), 1)

    def test_bad_idea(self):
        """ Test an incomplete POST submission to add an idea. """

        self.client.login(username='test1@example.com', password='1')
        self.assertEquals(models.Idea.objects.all().count(), 0)
        num_voters = get_user_model().objects.filter(vote__idea__pk=1, vote__vote=1).count()
        self.assertEqual(num_voters, 0)
        resp = self.client.post(reverse('idea:add_idea'), {'text':'test text'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('This field is required.', resp.content)
        self.assertEquals(models.Idea.objects.all().count(), 0)

        num_voters = get_user_model().objects.filter(vote__idea__pk=1, vote__vote=1).count()
        self.assertEqual(num_voters, 0)

    def test_must_be_logged_in(self):
        """ A user must be logged in to create an idea. """
        resp = self.client.post(reverse('idea:add_idea'), {'title':'test title', 'summary':'test summary', 'text':'test text', 'tags':'test, tags'})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('login', resp['Location'])
        self.assertEqual(models.Idea.objects.all().count(), 0)

    @patch('idea.views.render')
    def test_similar(self, render):
        """
        List of similar ideas should make sense.
        """
        class Mock():
            pass
        with patch('idea.views.more_like_text') as mlt:
            backend = connections['default'].get_backend()
            backend.clear()
            user = random_user()
            state = models.State.objects.get(name='Active')
            similar1 = models.Idea(creator=user, title='airplanes', state=state,
                    text="Title is enough said.")
            similar1.save()
            similar2 = models.Idea(creator=user, title='exexex', state=state,
                    text="I, too, love submarines.")
            similar2.save()

            models.Idea(creator=user, title='AAAAAA', state=state, 
                    text='BBBBBB').save()

            m1, m2 = Mock(), Mock()
            m1.object = similar1
            m2.object = similar2
            mlt.return_value = [m1, m2]

            views.add_idea(mock_req('/?idea_title=' +
                'Airplanes%20and%20submarines'))
            context = render.call_args[0][2]
            self.assertTrue('similar' in context)
            self.assertEqual(2, len(context['similar']))
            self.assertEqual(set(context['similar']), set([similar1, similar2]))

    @unittest.skipIf(COLLAB_TAGS == False, "TaggedItem creator field requires collab's core.taggit")
    def test_tagged_item_creator(self):
        """ Test tag fields from a normal POST submission to add an idea. """

        self.client.login(username='test1@example.com', password='1')
        self.assertEquals(models.Idea.objects.all().count(), 0)
        resp = self.client.post(reverse('idea:add_idea'), {'title':'test title', 'summary':'test summary', 'text':'test text', 'tags':'test, tags'})
        tagged_items = TaggedItem.objects.filter(content_type__name='idea')
        self.assertEqual(2, tagged_items.count())
        user = get_user_model().objects.get(username='test1@example.com')
        idea = models.Idea.objects.all()[0]
        for ti in tagged_items:
            self.assertEqual(user, ti.tag_creator)
        
    @patch('idea.views.render')
    def test_add_idea_with_banner(self, render):
        """
        Verify that the banner field auto-populates properly
        """

        banner1 = models.Banner(id=1, title="AAAA", text="text1",
                               start_date=date.today())
        banner1.save()
        banner2 = models.Banner(id=2, title="BBBB", text="text2",
                               start_date=date.today(),
                               end_date=date.today() + timedelta(days=1))
        banner2.save()
        banner3 = models.Banner(id=3, title="BBBB", text="text3",
                               start_date=date.today() - timedelta(days=2),
                               end_date=date.today() - timedelta(days=1))
        banner3.save()

        views.add_idea(mock_req())
        context = render.call_args[0][2]
        self.assertTrue('form' in context)
        self.assertTrue(isinstance(context['form'], IdeaForm))
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(None, selected)
        self.assertIn(banner1, banner_field._queryset)
        self.assertIn(banner2, banner_field._queryset)
        self.assertNotIn(banner3, banner_field._queryset)

        views.add_idea(mock_req(), banner1.id)
        context = render.call_args[0][2]
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(banner1, selected)
        self.assertIn(banner1, banner_field._queryset)
        self.assertIn(banner2, banner_field._queryset)
        self.assertNotIn(banner3, banner_field._queryset)

        views.add_idea(mock_req(), banner2.id)
        context = render.call_args[0][2]
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(banner2, selected)
        self.assertIn(banner1, banner_field._queryset)
        self.assertIn(banner2, banner_field._queryset)
        self.assertNotIn(banner3, banner_field._queryset)

        views.add_idea(mock_req(), banner3.id)
        context = render.call_args[0][2]
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(None, selected)
        self.assertIn(banner1, banner_field._queryset)
        self.assertIn(banner2, banner_field._queryset)
        self.assertNotIn(banner3, banner_field._queryset)

    @patch('idea.views.render')
    def test_add_idea_with_no_banner(self, render):
        """
        Verify that the banner field disappears if no current challenge
        """

        banner1 = models.Banner(id=1, title="AAAA", text="text1",
                               start_date=date.today() - timedelta(days=2),
                               end_date=date.today() - timedelta(days=1))
        banner1.save()
        banner2 = models.Banner(id=2, title="BBBB", text="text2",
                               start_date=date.today() + timedelta(days=1))
        banner2.save()

        views.add_idea(mock_req())
        context = render.call_args[0][2]
        self.assertTrue('form' in context)
        self.assertTrue(isinstance(context['form'], IdeaForm))
        self.assertNotIn('banner', context['form'].fields.keys())
