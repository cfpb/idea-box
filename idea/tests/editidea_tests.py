from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from idea import models, views
from idea.forms import IdeaForm, PrivateIdeaForm
from idea.tests.utils import mock_req, random_user, login, create_superuser
from datetime import date
from mock import patch

def create_idea(user=None):
    if not user:
        user = random_user()
    state = models.State.objects.get(name='Active')
    idea = models.Idea(creator=user, title='Transit subsidy to Mars', 
                text='Aliens need assistance.', state=state)
    banner = models.Banner(id=1, title="AAAA", text="text1",
                           start_date=date.today())
    banner.save()
    idea.banner = banner
    idea.save()
    idea.tags.add("test tag")
    return idea

class EditIdeaTest(TestCase):
    fixtures = ['state']

    def setUp(self):
        create_superuser()

    def test_edit_good_idea(self):
        """ Test an normal POST submission to edit an idea. """
        user = login(self)
        idea = create_idea(user=user)

        self.assertEquals(models.Idea.objects.all().count(), 1)
        new_title = "new title"
        new_summary = "new summary"
        new_text = "new text"
        new_banner = models.Banner(id=2, title="BBB", text="text2",
                                   start_date=date.today())
        new_banner.save()
        resp = self.client.post(reverse('idea:edit_idea', args=(idea.id,)),
                                        {'title':new_title,
                                         'summary':new_summary,
                                         'text':new_text,
                                         'banner': new_banner.id})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('detail', resp['Location'])
        self.assertEquals(models.Idea.objects.all().count(), 1)

        # ensure editing an idea does not up the vote count
        # vote count is 0 because votes are added in views.add_idea, which is not used in this test
        num_voters = get_user_model().objects.filter(vote__idea__pk=idea.id, vote__vote=1).count()
        self.assertEqual(num_voters, 0)

        refresh_idea = models.Idea.objects.get(id=idea.id)
        self.assertEqual(refresh_idea.title, new_title)
        self.assertEqual(refresh_idea.summary, new_summary)
        self.assertEqual(refresh_idea.text, new_text)
        self.assertEqual(refresh_idea.banner, new_banner)

        # verify the expected fields remain the same
        self.assertEqual(refresh_idea.tags.count(), 1)
        self.assertEqual(refresh_idea.tags.all()[0].name, "test tag")
        self.assertEqual(refresh_idea.creator, idea.creator)

    def test_bad_edit_idea(self):
        """ Test an incomplete POST submission to edit an idea. """
        user = login(self)
        idea = create_idea(user=user)

        resp = self.client.post(reverse('idea:edit_idea', args=(idea.id,)), {'text':'new title'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('This field is required.', resp.content)
        self.assertEquals(models.Idea.objects.all().count(), 1)

        refresh_idea = models.Idea.objects.get(id=idea.id)
        self.assertEqual(refresh_idea.title, idea.title)
        self.assertEqual(refresh_idea.banner, idea.banner)

    def test_must_be_logged_in(self):
        """ A user must be logged in to edit an idea. """
        user = login(self)
        idea = create_idea(user=user)
        self.client.logout()
        resp = self.client.post(reverse('idea:edit_idea', args=(idea.id,)), {'title':'test title', 'summary':'test summary', 'text':'test text'})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('login', resp['Location'])

    def test_edit_ignores_tags(self):
        """ A user must be logged in to edit an idea. """

        user = login(self)
        idea = create_idea(user=user)
        resp = self.client.post(reverse('idea:edit_idea', args=(idea.id,)), {'title':'test title', 'summary':'test summary', 'text':'test text', 'tags':'sample, newtag'})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('detail', resp['Location'])

        refresh_idea = models.Idea.objects.get(id=idea.id)
        self.assertEqual(refresh_idea.tags.count(), 1)
        self.assertEqual(refresh_idea.tags.all()[0].name, "test tag")

    @patch('idea.views.render')
    def test_edit_idea_with_private_banner(self, render):
        """
        Verify that the private banner field auto-populates properly
        """
        user = login(self)
        state = models.State.objects.get(name='Active')

        idea1 = models.Idea(creator=user, title='Transit subsidy to Venus', 
                            text='Aliens need assistance.', state=state)
        banner1 = models.Banner(id=1, title="AAAA", text="text1",
                                start_date=date.today(), is_private=True)
        banner1.save()
        idea1.banner = banner1
        idea1.save()

        idea2 = models.Idea(creator=user, title='Transit subsidy to Venus', 
                            text='Aliens need assistance.', state=state)
        banner2 = models.Banner(id=2, title="BBBB", text="text2",
                                start_date=date.today())
        banner2.save()
        idea2.banner = banner2
        idea2.save()

        views.edit_idea(mock_req(user=user), idea1.id)
        context = render.call_args[0][2]
        self.assertTrue('form' in context)
        self.assertTrue(isinstance(context['form'], PrivateIdeaForm))
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(banner1.id, selected)
        self.assertEqual(context['form'].fields['banner'].widget.choices.field.empty_label, None)
        self.assertIn(banner1, banner_field._queryset)
        self.assertNotIn(banner2, banner_field._queryset)

        views.edit_idea(mock_req(user=user), idea2.id)
        context = render.call_args[0][2]
        self.assertTrue('form' in context)
        self.assertTrue(isinstance(context['form'], IdeaForm))
        self.assertFalse(isinstance(context['form'], PrivateIdeaForm))
        banner_field = context['form'].fields['banner']
        selected = context['form'].initial['banner']
        self.assertEqual(banner2.id, selected)
        self.assertEqual(context['form'].fields['banner'].widget.choices.field.empty_label, 'Select')
        self.assertNotIn(banner1, banner_field._queryset)
        self.assertIn(banner2, banner_field._queryset)
