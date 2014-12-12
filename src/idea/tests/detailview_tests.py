from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import TestCase
from django.test.client import RequestFactory
from idea import models, views
from idea.forms import IdeaTagForm
from django.core.urlresolvers import reverse
from idea.tests.utils import mock_req, random_user, create_superuser, login
from mock import patch
import random

class DetailViewTest(TestCase):
    """
    Tests for idea.views.detail.
    """
    fixtures = ['state']
    def test_404s(self):
        """
        Should get a 404 when using a bad idea_id.
        """
        user = get_user_model().objects.create_user('example')
        state = models.State.objects.get(name='Active')
        idea = models.Idea(creator=user, title='title', text='text',
                state=state)
        idea.save()
        self.assertRaises(Http404, views.detail, mock_req(), '1234')
        #   No need to test other strings; we only match regex with digits

    @patch('idea.views.render')
    def test_idea_correct(self, render):
        """
        The idea passed to the ui should be that identified by the id.
        """
        user = get_user_model().objects.create_user('example')
        state = models.State.objects.get(name='Active')
        idea1 = models.Idea(creator=user, title='title', text='text',
                state=state)
        idea2 = models.Idea(creator=user, title='title', text='text',
                state=state)
        idea1.save()
        idea2.save()
        views.detail(mock_req(), str(idea2.id))
        context = render.call_args[0][2]
        self.assertTrue('idea' in context)
        self.assertEqual(idea2.id, context['idea'].id)
        self.assertEqual(idea2.title, context['idea'].title)

    @patch('idea.views.render')
    def test_idea_voters(self, render):
        """
        The idea passed to the ui should have the correct voters.
        """
        user = get_user_model().objects.create_user('example')
        state = models.State.objects.get(name='Active')
        idea = models.Idea(creator=user, title='title', text='text',
                state=state)
        idea.save()

        users = []
        for i in range(5):
            users.append(get_user_model().objects.create_user('example' + str(i)))
            models.Vote(creator=users[i], idea=idea).save()

        views.detail(mock_req(), str(idea.id))
        context = render.call_args[0][2]
        self.assertTrue('voters' in context)
        self.assertEqual(5, len(context['voters']))
        self.assertEqual(set([u.id for u in users]),
                set([v.id for v in context['voters']]))

    @patch('idea.views.render')
    def test_idea_support(self, render):
        """
        Check support = True if voted votes.
        """
        user = random_user()
        state = models.State.objects.get(name='Active')
        idea = models.Idea(creator=user, title='title', text='text',
                state=state)
        idea.save()

        voter = random_user()
        models.Vote(creator=voter, idea=idea).save()

        views.detail(mock_req(user=voter), str(idea.id))
        context = render.call_args[0][2]
        self.assertTrue('support' in context)
        self.assertTrue(context['support'])

    @patch('idea.views.render')
    def test_idea_no_support(self, render):
        """
        Check support = False if no votes.
        """
        user = random_user()
        state = models.State.objects.get(name='Active')
        idea = models.Idea(creator=user, title='title', text='text',
                state=state)
        idea.save()

        for _ in range(7):
            models.Vote(creator=random_user(), idea=idea).save()

        views.detail(mock_req(), str(idea.id))
        context = render.call_args[0][2]
        self.assertTrue('support' in context)
        self.assertFalse(context['support'])

    @patch('idea.views.render')
    def test_tags(self, render):
        """
        Include a sorted list of tags for this idea.
        """
        user = random_user()
        state = models.State.objects.get(name='Active')
        idea = models.Idea(creator=user, title='title', text='text',
                state=state)
        idea.save()

        tags = [str(random.randint(11111, 99999)) for _ in range(20)]
        idea.tags.add(*tags)

        views.detail(mock_req(), str(idea.id))
        context = render.call_args[0][2]
        self.assertTrue('tags' in context)
        self.assertEqual(20, len(context['tags']))

        tags.sort()
        self.assertEqual(tags, [tag.name for tag in context['tags']])

    @patch('idea.views.render')
    def test_tag_form_exists(self, render):
        """
        Detail page should have a form for adding tags.
        """
        idea = models.Idea(creator=random_user(), title='AAAA',
                state = models.State.objects.get(name='Active'))
        idea.save()

        views.detail(mock_req(), str(idea.id))
        context = render.call_args[0][2]
        self.assertTrue('tag_form' in context)
        self.assertTrue(isinstance(context['tag_form'], IdeaTagForm))

    def test_tag_form_submission(self):
        """
        Detail page tag form submission should add tags.
        """
        idea = models.Idea(creator=random_user(), title='AAAA',
                state = models.State.objects.get(name='Active'))
        idea.save()
        idea.tags.add('aaa', 'bbb', 'ccc')

        req = RequestFactory().post('/', {'tags': 'DDD, EEE, ZZZ,'})
        req.user = random_user()
        views.detail(req, str(idea.id))

        idea = models.Idea.objects.get(id = idea.id)
        tags = set([tag.name for tag in idea.tags.all()])
        self.assertEqual(set(['aaa', 'bbb', 'ccc', 'ddd', 'eee', 'zzz']),
                tags)

    def test_anonymous_idea_hidden_name(self):
        user = random_user()
        state = models.State.objects.get(name='Active')
        state.save()
        idea = models.Idea(creator=user, title='AAAA', text='AA Text',
                           state=state)
        idea.save()

        create_superuser()
        login(self)
        resp = self.client.get(reverse('idea:idea_detail', args=(idea.id,)))
        self.assertTrue(user.first_name in resp.content)

        idea2 = models.Idea(creator=user, title='BBBB', text='BB Text',
                            state=state, is_anonymous=True)
        idea2.save()

        resp = self.client.get(reverse('idea:idea_detail', args=(idea2.id,)))
        self.assertFalse(user.first_name in resp.content)
