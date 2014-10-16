from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from idea import models
from idea.tests.utils import random_user, login, create_superuser
from datetime import date

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

class AddIdeaTest(TestCase):
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
