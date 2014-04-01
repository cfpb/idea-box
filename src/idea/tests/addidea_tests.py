from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from haystack import connections
from idea import models, views
from idea.tests.utils import mock_req, random_user
from mock import patch


class AddIdeaTest(TestCase):
    fixtures = ['state', 'core-test-fixtures']

    def test_good_idea(self):
        """ Test an normal POST submission to add an idea. """

        self.client.login(username='test1@example.com', password='1')
        self.assertEquals(models.Idea.objects.all().count(), 0)
        num_voters = User.objects.filter(vote__idea__pk=1, vote__vote=1).count()
        self.assertEqual(num_voters, 0)
        resp = self.client.post(reverse('idea:add_idea'), {'title':'JSON format for HMDA data', 'text':'HMDA data in JSON format. '})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('detail', resp['Location'])
        self.assertEquals(models.Idea.objects.all().count(), 1)

        num_voters = User.objects.filter(vote__idea__pk=1, vote__vote=1).count()
        self.assertEqual(num_voters, 1)

    def test_must_be_logged_in(self):
        """ A user must be logged in to create an idea. """
        resp = self.client.post(reverse('idea:add_idea'), {'title':'JSON format for HMDA data', 'text':'HMDA data in JSON format. '})
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

