from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
from django.utils import unittest
from idea import models, views
from idea.tests.utils import mock_req, random_user, login, create_superuser
from mock import patch
from datetime import date, timedelta
from idea.forms import IdeaForm, PrivateIdeaForm

if 'core.taggit' in settings.INSTALLED_APPS:
    from core.taggit.utils import add_tags
    from core.taggit.models import TaggedItem
    COLLAB_TAGS = True;
else:
    COLLAB_TAGS = False;

class AddIdeaTest(TestCase):
    fixtures = ['state']

    def setUp(self):
        create_superuser()

    def test_good_idea(self):
        """ Test an normal POST submission to add an idea. """
        login(self)
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
        login(self)
        self.assertEquals(models.Idea.objects.all().count(), 0)
        resp = self.client.post(reverse('idea:add_idea'), {'title':'test title', 'summary':'test summary', 'text':'test text', 'tags':'test, tags'})
        self.assertEquals(models.Idea.objects.all().count(), 1)
        resp = self.client.post(reverse('idea:add_idea'), {'title':'test title', 'summary':'new summary', 'text':'new text', 'tags':'new, tags'})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('detail', resp['Location'])
        self.assertEquals(models.Idea.objects.all().count(), 1)

    def test_bad_idea(self):
        """ Test an incomplete POST submission to add an idea. """

        login(self)
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

    @unittest.skipIf(COLLAB_TAGS == False, "TaggedItem creator field requires collab's core.taggit")
    def test_tagged_item_creator(self):
        """ Test tag fields from a normal POST submission to add an idea. """

        user = login(self)
        self.assertEquals(models.Idea.objects.all().count(), 0)
        resp = self.client.post(reverse('idea:add_idea'), {'title':'test title', 'summary':'test summary', 'text':'test text', 'tags':'test, tags'})
        tagged_items = TaggedItem.objects.filter(content_type__name='idea')
        self.assertEqual(2, tagged_items.count())
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
        self.assertEqual(context['form'].fields['banner'].widget.choices.field.empty_label, 'Select')
        self.assertIn(banner1, banner_field._queryset)
        self.assertIn(banner2, banner_field._queryset)
        self.assertNotIn(banner3, banner_field._queryset)

        views.add_idea(mock_req(), banner1.id)
        context = render.call_args[0][2]
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(banner1.id, selected)
        self.assertEqual(context['form'].fields['banner'].widget.choices.field.empty_label, 'Select')
        self.assertIn(banner1, banner_field._queryset)
        self.assertIn(banner2, banner_field._queryset)
        self.assertNotIn(banner3, banner_field._queryset)

        views.add_idea(mock_req(), banner2.id)
        context = render.call_args[0][2]
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(banner2.id, selected)
        self.assertEqual(context['form'].fields['banner'].widget.choices.field.empty_label, 'Select')
        self.assertIn(banner1, banner_field._queryset)
        self.assertIn(banner2, banner_field._queryset)
        self.assertNotIn(banner3, banner_field._queryset)

        views.add_idea(mock_req(), banner3.id)
        context = render.call_args[0][2]
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(None, selected)
        self.assertEqual(context['form'].fields['banner'].widget.choices.field.empty_label, 'Select')
        self.assertIn(banner1, banner_field._queryset)
        self.assertIn(banner2, banner_field._queryset)
        self.assertNotIn(banner3, banner_field._queryset)

    @patch('idea.views.render')
    def test_add_idea_with_private_banner(self, render):
        """
        Verify that the private banner field auto-populates properly
        """

        banner1 = models.Banner(id=1, title="AAAA", text="text1",
                               start_date=date.today(), is_private=True)
        banner1.save()
        banner2 = models.Banner(id=2, title="BBBB", text="text2",
                               start_date=date.today())
        banner2.save()

        views.add_idea(mock_req())
        context = render.call_args[0][2]
        self.assertTrue('form' in context)
        self.assertTrue(isinstance(context['form'], IdeaForm))
        self.assertFalse(isinstance(context['form'], PrivateIdeaForm))
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(None, selected)
        self.assertEqual(context['form'].fields['banner'].widget.choices.field.empty_label, 'Select')
        self.assertNotIn(banner1, banner_field._queryset)
        self.assertIn(banner2, banner_field._queryset)

        views.add_idea(mock_req(), banner1.id)
        context = render.call_args[0][2]
        self.assertTrue(isinstance(context['form'], PrivateIdeaForm))
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(banner1.id, selected)
        self.assertEqual(context['form'].fields['banner'].widget.choices.field.empty_label, None)
        self.assertIn(banner1, banner_field._queryset)
        self.assertNotIn(banner2, banner_field._queryset)

        views.add_idea(mock_req(), banner2.id)
        context = render.call_args[0][2]
        self.assertTrue(isinstance(context['form'], IdeaForm))
        self.assertFalse(isinstance(context['form'], PrivateIdeaForm))
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(context['form'].fields['banner'].widget.choices.field.empty_label, 'Select')
        self.assertEqual(banner2.id, selected)
        self.assertNotIn(banner1, banner_field._queryset)
        self.assertIn(banner2, banner_field._queryset)

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

    @patch('idea.views.render')
    def test_add_idea_with_anonymous_option(self, render):
        """
        Verify that the anonymous field auto-populates only for
        ideas where banner is preset and the banner is private
        """

        banner1 = models.Banner(id=1, title="AAAA", text="text1",
                                start_date=date.today(), is_private=True)
        banner1.save()
        banner2 = models.Banner(id=2, title="BBBB", text="text2",
                                start_date=date.today())
        banner2.save()

        views.add_idea(mock_req(), banner1.id)
        context = render.call_args[0][2]
        self.assertTrue(isinstance(context['form'], PrivateIdeaForm))
        self.assertIn("is_anonymous", context['form'].fields)
        self.assertNotIn("is_anonymous", context['form'].initial)

        views.add_idea(mock_req(), banner2.id)
        context = render.call_args[0][2]
        self.assertTrue(isinstance(context['form'], IdeaForm))
        self.assertNotIn("is_anonymous", context['form'].fields)
        self.assertNotIn("is_anonymous", context['form'].initial)
