import datetime
from core.custom_comments.forms import MPTTCommentForm
from core.custom_comments.models import MPTTComment
from django.test import TestCase
from django.core.urlresolvers import reverse
from idea import models
from idea.tests.utils import random_user, create_superuser, login


def create_banner(title, delta_days=0, is_private=False):
    banner = models.Banner(title=title, text=title+' Text', is_private=is_private,
                           start_date=datetime.datetime.now())
    banner.save()
    return banner


def create_idea():
    user = random_user()
    state = models.State.objects.get(name='Active')
    state.save()
    idea = models.Idea(creator=user, title='AAAA', text='AA Text', state=state)
    idea.save()
    return idea

def get_valid_form_data(obj):
    f = MPTTCommentForm(obj)
    data = {}
    data['comment'] = "sample comment"
    user = random_user()
    data['name'] = user.username
    data['email'] = user.email
    data.update(f.initial)
    return data

class CommentTest(TestCase):
    """
    Tests for core.custom_comments.MPTTComment
    """
    fixtures = ['state']

    def test_not_anonymous_form(self):
        idea = create_idea()
        data = get_valid_form_data(idea)

        f = MPTTCommentForm(idea, data=data)
        c = f.get_comment_object()
        self.assertTrue(isinstance(c, MPTTComment))
        self.assertEqual(c.is_anonymous, False)

    def test_anonymous_form(self):
        idea = create_idea()
        data = get_valid_form_data(idea)
        data['is_anonymous'] = True

        f = MPTTCommentForm(idea, data=data)
        c = f.get_comment_object()
        self.assertTrue(isinstance(c, MPTTComment))
        self.assertEqual(c.is_anonymous, True)
        # (It is up to the front end to hide the name)
        self.assertEqual(c.user_name, data['name'])

    def test_anonymous_checkbox_exists(self):
        """
        Detail page should have an anonymous checkbox for ideas with a private
        banner
        """
        banner = models.Banner(id=1, title="XXXX", text="text",
                               is_private=True,
                               start_date=datetime.date.today())
        banner.save()

        idea = models.Idea(creator=random_user(), title='AAAA', banner=banner,
                           state=models.State.objects.get(name='Active'))
        idea.save()

        create_superuser()
        login(self)
        resp = self.client.get(reverse('idea:idea_detail', args=(idea.id,)))
        self.assertTrue('id_is_anonymous' in resp.content)

    def test_anonymous_checkbox_absent(self):
        """
        Detail page should NOT have an anonymous checkbox for non-private
        banners and ideas without a banner
        """
        banner = models.Banner(id=1, title="XXXX", text="text",
                               is_private=False,
                               start_date=datetime.date.today())
        banner.save()

        idea = models.Idea(creator=random_user(), title='AAAA', banner=banner,
                           state=models.State.objects.get(name='Active'))
        idea.save()

        create_superuser()
        login(self)
        resp = self.client.get(reverse('idea:idea_detail', args=(idea.id,)))
        self.assertFalse('id_is_anonymous' in resp.content)

        idea2 = models.Idea(creator=random_user(), title='BBBB', banner=None,
                            state=models.State.objects.get(name='Active'))
        idea2.save()

        resp = self.client.get(reverse('idea:idea_detail', args=(idea2.id,)))
        self.assertFalse('id_is_anonymous' in resp.content)

    def test_anonymous_comment_hidden_name(self):
        idea = create_idea()
        data = get_valid_form_data(idea)
        data['is_anonymous'] = True

        f = MPTTCommentForm(idea, data=data)
        c = f.get_comment_object()
        c.save()

        create_superuser()
        login(self)
        resp = self.client.get(reverse('idea:idea_detail', args=(idea.id,)))
        self.assertFalse(data['name'] in resp.content)

        # add a second comment where anonymous = False
        data['is_anonymous'] = False
        data['comment'] = "new comment"
        f = MPTTCommentForm(idea, data=data)
        c = f.get_comment_object()
        c.save()

        resp = self.client.get(reverse('idea:idea_detail', args=(idea.id,)))
        self.assertTrue(data['name'] in resp.content)
