from datetime import datetime
from django.contrib.auth.models import User
from django.utils.timezone import get_default_timezone
from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.test import TestCase
from idea import models, views
from idea.tests.utils import mock_req, random_user
from mock import patch
import string

class ListViewTest(TestCase):
    """
    Tests for idea.views.list
    """
    fixtures = ['state']
    def _generate_data(self, paramfn=lambda x,y:None, postfn=lambda x,y:None,
            entry_data=[(5, 'AAAA'), (9, 'BBBB'), (3, 'CCCC'), (7, 'DDDD'),
                        (1, 'EEEE'), (11, 'FFFF')]):
        """
        Helper function to handle the idea (and related models) creation.
        """
        user = User.objects.create_user('example')
        state = models.State.objects.get(name='Active')
        state.save()

        def make_idea(nonce, title):
            kwargs = {'creator': user, 'title': title, 
                    'text': title + ' Text', 'state': state}
            paramfn(kwargs, nonce)
            idea = models.Idea(**kwargs)
            idea.save()
            postfn(idea, nonce)
            return idea

        ideas = [make_idea(pair[0], pair[1]) for pair in entry_data]

    def _verify_order(self, render):
        """
        Given a patched render, verify the order of the ideas.
        """
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(6, len(context['ideas']))
        self.assertEqual('FFFF', context['ideas'][0].title)
        self.assertEqual('BBBB', context['ideas'][1].title)
        self.assertEqual('DDDD', context['ideas'][2].title)
        self.assertEqual('AAAA', context['ideas'][3].title)
        self.assertEqual('CCCC', context['ideas'][4].title)
        self.assertEqual('EEEE', context['ideas'][5].title)

    @patch('idea.views.render')
    def test_sort_recent(self, render):
        """
        Verify that the recent sort params works.
        """
        def add_time(kwargs, nonce):
            kwargs['time'] = datetime(2013, 1, nonce, tzinfo=get_default_timezone())
        self._generate_data(paramfn=add_time)
        views.list(mock_req(), sort_or_state='recent')
        self._verify_order(render)

    @patch('idea.views.render')
    def test_sort_trending(self, render):
        """
        Verify that the comments sort works.
        """
        idea_type = ContentType.objects.get(app_label="idea", model="idea")
        site = Site.objects.get_current()
        def add_time(kwargs, nonce):
            # add future timestamp for item 3
            if nonce == 3:
                kwargs['time'] = datetime(2050, 1, nonce, tzinfo=get_default_timezone())
        def create_timestamp_event(idea, nonce):
            # add future timestamp for vote for items 0, 2, 4
            if nonce % 2 == 0:
                models.Vote(creator=idea.creator,
                            idea=idea,
                            time=datetime(2050, 1, nonce, tzinfo=get_default_timezone())
                           ).save()
            # add future timestamp for comment for items 1, 5
            elif nonce != 3:
                Comment(content_type=idea_type, site=site,
                        object_pk=idea.pk, user=idea.creator,
                        comment='Blah',
                        submit_date=datetime(2050, 1, nonce, tzinfo=get_default_timezone())
                       ).save()
        self._generate_data(postfn=create_timestamp_event, paramfn=add_time)
        views.list(mock_req(), sort_or_state='trending')
        self._verify_order(render)

    @patch('idea.views.render')
    def test_sort_vote(self, render):
        """
        Verify that the votes sort works.
        """
        def create_votes(idea, nonce):
            for _ in range(nonce):
                models.Vote(creator=idea.creator, idea=idea).save()
        self._generate_data(postfn=create_votes)
        views.list(mock_req(), sort_or_state='vote')
        self._verify_order(render)

    @patch('idea.views.render')
    def test_paging(self, render):
        """
        Verify that paging works as we would expect.
        """
        letters = string.uppercase
        entry_data = []
        ## current default ordering is based on most recently modified
        ## Count down from 12 to 1, so A has the most recent timestamp
        for i in range(12, -1, -1):
            entry_data.append((i+1, letters[i]*4))
        self._generate_data(entry_data=entry_data)

        views.list(mock_req())
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(10, len(context['ideas']))
        self.assertEqual('AAAA', context['ideas'][0].title)
        self.assertEqual('EEEE', context['ideas'][4].title)

        views.list(mock_req('/?page_num=1'))
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(10, len(context['ideas']))
        self.assertEqual('AAAA', context['ideas'][0].title)
        self.assertEqual('EEEE', context['ideas'][4].title)

        views.list(mock_req('/?page_num=sadasds'))
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(10, len(context['ideas']))
        self.assertEqual('AAAA', context['ideas'][0].title)
        self.assertEqual('EEEE', context['ideas'][4].title)

        views.list(mock_req('/?page_num=2'))
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(3, len(context['ideas']))
        self.assertEqual('KKKK', context['ideas'][0].title)
        self.assertEqual('MMMM', context['ideas'][2].title)

        views.list(mock_req('/?page_num=232432'))
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(3, len(context['ideas']))
        self.assertEqual('KKKK', context['ideas'][0].title)
        self.assertEqual('MMMM', context['ideas'][2].title)
    
    @patch('idea.views.render')
    def test_idea_fields(self, render):
        """
        Verify that the fields needed by the ui are available on all ideas.
        """
        self._generate_data()

        views.list(mock_req())
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(6, len(context['ideas']))
        for idea in context['ideas']:
            self.assertTrue(hasattr(idea, 'title'))
            self.assertTrue(hasattr(idea, 'url'))
            self.assertTrue(hasattr(idea.creator, 'first_name'))
            self.assertTrue(hasattr(idea.creator, 'last_name'))
            #self.assertTrue(hasattr(idea.creator, 'photo'))
            #self.assertTrue(hasattr(idea, 'comment_count'))
            self.assertTrue(hasattr(idea, 'vote_count'))
            self.assertTrue(hasattr(idea, 'time'))

    @patch('idea.views.render')
    def test_idea_state_filter(self, render):
        """
        Verify that state filters work as we expect.
        """
        def check_state(kwargs, nonce):
            if nonce % 2 == 0:
                kwargs['state'] = models.State.objects.get(name='Archive')

        self._generate_data(entry_data=[(1,'AAAA'), (2,'BBBB'), (3,'CCCC')],
                paramfn=check_state)

        #   defaults to active
        views.list(mock_req())
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(2, len(context['ideas']))

        #   But archive works
        views.list(mock_req(), sort_or_state='archived')
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(1, len(context['ideas']))

    @patch('idea.views.render')
    def test_tags_exist(self, render):
        """
        Check that the tag list is populated and only shows the top ten
        tags.
        """
        user = random_user()
        state = models.State.objects.get(name='Active')
        state.save()

        idea = models.Idea(creator=user, title='AAAA', text='AAAA Text',
                state=state)
        idea.save()

        idea.tags.add('bbb', 'ccc', 'ddd')
        views.list(mock_req())
        context = render.call_args[0][2]
        self.assertTrue('tags' in context)
        self.assertEqual(3, len(context['tags']))
        self.assertEqual(set(['bbb', 'ccc', 'ddd']), 
                set([t.name for t in context['tags']]))

    @patch('idea.views.render')
    def test_tags_top_list(self, render):
        """
        Tag list should be in proper order.
        """
        user = random_user()
        state = models.State.objects.get(name='Active')
        state.save()

        #   Make 13 tags, and assign each to a set of ideas
        for count in range(30):
            tag = str(count)*4
            for i in range(count+1):
                idea = models.Idea(creator=user, title=str(i)*4, 
                        text=str(i)*4 +' Text', state=state)
                idea.save()
                idea.tags.add(tag)

        views.list(mock_req())
        context = render.call_args[0][2]
        self.assertTrue('tags' in context)
        self.assertEqual(25, len(context['tags']))
        # 29292929, 28282828, 27272727, ...
        self.assertEqual([str(i)*4 for i in range(29,4,-1)],
                [t.name for t in context['tags']])

    @patch('idea.views.render')
    def test_tags_count(self, render):
        """
        Tag list should include tag count.
        """
        user = random_user()
        state = models.State.objects.get(name='Active')
        state.save()

        #   Make 13 tags, and assign each to a set of ideas
        for count in range(13):
            tag = str(count)*4
            for i in range(count+1):
                idea = models.Idea(creator=user, title=str(i)*4, 
                        text=str(i)*4 +' Text', state=state)
                idea.save()
                idea.tags.add(tag)

        views.list(mock_req())
        context = render.call_args[0][2]
        self.assertTrue('tags' in context)

        for i in range(12,2,-1):
            tag = context['tags'][12-i]
            self.assertTrue(hasattr(tag, 'count'))
            self.assertEqual(i+1, tag.count)

    @patch('idea.views.render')
    def test_tags_active(self, render):
        """
        Tag list should include if tag was active in this search.
        """
        def add_tag(idea, nonce):
            tag = str(nonce % 3)
            idea.tags.add(tag)
        self._generate_data(postfn=add_tag)

        views.list(mock_req())
        context = render.call_args[0][2]
        self.assertTrue('tags' in context)
        for tag in context['tags']:
            self.assertFalse(tag.active)

        views.list(mock_req('/?tags=0'))
        context = render.call_args[0][2]
        for tag in context['tags']:
            self.assertEqual(tag.name == '0', tag.active)

        views.list(mock_req('/?tags=1'))
        context = render.call_args[0][2]
        for tag in context['tags']:
            self.assertEqual(tag.name == '1', tag.active)

        views.list(mock_req('/?tags=1,2'))
        context = render.call_args[0][2]
        for tag in context['tags']:
            self.assertEqual(tag.name in ['1','2'], tag.active)


    @patch('idea.views.render')
    def test_tag_filter(self, render):
        """
        List of ideas should be filterable by tag.
        """
        def add_tag(idea, nonce):
            tag = str(nonce % 3)
            idea.tags.add(tag)
        self._generate_data(postfn=add_tag)

        views.list(mock_req())
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(6, len(context['ideas']))

        views.list(mock_req('/?tags=0'))
        context = render.call_args[0][2]
        self.assertEqual(2, len(context['ideas']))
        self.assertEqual(set(['BBBB', 'CCCC']), 
                set([i.title for i in context['ideas']]))

        views.list(mock_req('/?tags=1'))
        context = render.call_args[0][2]
        self.assertEqual(2, len(context['ideas']))
        self.assertEqual(set(['DDDD', 'EEEE']), 
                set([i.title for i in context['ideas']]))

        views.list(mock_req('/?tags=1,2'))
        context = render.call_args[0][2]
        self.assertEqual(4, len(context['ideas']))
        self.assertEqual(set(['DDDD', 'AAAA', 'EEEE', 'FFFF']), 
                set([i.title for i in context['ideas']]))

