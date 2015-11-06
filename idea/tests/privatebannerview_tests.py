import datetime
from django.contrib.auth import get_user_model
from django.utils.timezone import get_default_timezone
from django.test import TestCase
from idea import models, views
from idea.tests.utils import mock_req, random_user
from mock import patch
import string

def get_relative_date(delta_days=0):
    return datetime.date.today() + datetime.timedelta(days=delta_days)

class PrivateBannerViewTest(TestCase):
    """
    Tests for idea.views.room_detail
    """
    fixtures = ['state']
    def _generate_data(self, paramfn=lambda x,y:None, postfn=lambda x,y:None,
            entry_data=[(5, 'AAAA'), (9, 'BBBB'), (3, 'CCCC'), (7, 'DDDD'),
                        (1, 'EEEE'), (11, 'FFFF')]):
        """
        Helper function to handle the idea (and related models) creation.
        """
        user = get_user_model().objects.create_user('example')
        state = models.State.objects.get(name='Active')
        state.save()

        banner = models.Banner(id=1, title="XXXX", text="text", is_private=True,
                               start_date=datetime.date.today())
        banner.save()

        def make_idea(nonce, title, banner=banner):
            kwargs = {'creator': user, 'title': title, 'banner': banner,
                    'text': title + ' Text', 'state': state}
            paramfn(kwargs, nonce)
            idea = models.Idea(**kwargs)
            idea.save()
            postfn(idea, nonce)
            return idea

        if entry_data:
            ideas = [make_idea(pair[0], pair[1]) for pair in entry_data]

        extra_ideas = [make_idea(pair[0], pair[1], pair[2]) \
                      for pair in [(24, 'ZZZZ', None), (25,'YYYY', None)]]

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
    def test_private_sort(self, render):
        """
        Verify sort order.
        """
        def add_time(kwargs, nonce):
            kwargs['time'] = datetime.datetime(2013, 1, nonce, tzinfo=get_default_timezone())
        self._generate_data(paramfn=add_time)
        views.room_detail(mock_req(), slug='xxxx')
        self._verify_order(render)

    @patch('idea.views.render')
    def test_private_paging(self, render):
        """
        Verify that paging works as we would expect.
        """
        letters = string.uppercase
        entry_data = []
        ## Count down from 12 to 1, so A has the most recent timestamp
        for i in range(12, -1, -1):
            entry_data.append((i+1, letters[i]*4))
        self._generate_data(entry_data=entry_data)

        views.room_detail(mock_req(), slug='xxxx')
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(10, len(context['ideas']))
        self.assertEqual('AAAA', context['ideas'][0].title)
        self.assertEqual('EEEE', context['ideas'][4].title)

        views.room_detail(mock_req('/?page_num=1'), slug='xxxx')
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(10, len(context['ideas']))
        self.assertEqual('AAAA', context['ideas'][0].title)
        self.assertEqual('EEEE', context['ideas'][4].title)

        views.room_detail(mock_req('/?page_num=sadasds'), slug='xxxx')
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(10, len(context['ideas']))
        self.assertEqual('AAAA', context['ideas'][0].title)
        self.assertEqual('EEEE', context['ideas'][4].title)

        views.room_detail(mock_req('/?page_num=2'), slug='xxxx')
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(3, len(context['ideas']))
        self.assertEqual('KKKK', context['ideas'][0].title)
        self.assertEqual('MMMM', context['ideas'][2].title)

        views.room_detail(mock_req('/?page_num=232432'), slug='xxxx')
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(3, len(context['ideas']))
        self.assertEqual('KKKK', context['ideas'][0].title)
        self.assertEqual('MMMM', context['ideas'][2].title)
    
    @patch('idea.views.render')
    def test_private_idea_fields(self, render):
        """
        Verify that the fields needed by the ui are available on all ideas.
        """
        self._generate_data()

        views.room_detail(mock_req(), slug='xxxx')
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
    def test_private_tags_exist(self, render):
        """
        Check that the tag list is populated with ONLY tags from private belonging ideas.
        """
        user = random_user()
        state = models.State.objects.get(name='Active')
        state.save()

        self._generate_data(entry_data=None)

        # create some dummy tags that are not part of this banner's ideas
        banner = models.Banner(id=2, title="XXXX", text="text", is_private=False,
                               start_date=datetime.date.today())
        banner.save()
        for count in range(2):
            tag = str(count)*4
            for i in range(count+1):
                idea = models.Idea(creator=user, title=str(i)*4+'3', 
                        text=str(i)*4 +'3 Text', state=state, banner_id=2)
                idea.save()
                idea.tags.add(tag)
        banner = models.Banner(id=3, title="XXXX", text="text", is_private=True,
                               start_date=datetime.date.today())
        banner.save()
        for count in range(2):
            tag = str(count)*4
            for i in range(count+1):
                idea = models.Idea(creator=user, title=str(i)*4+'4', 
                        text=str(i)*4 +'4 Text', state=state, banner_id=3)
                idea.save()
                idea.tags.add(tag)

        idea = models.Idea(creator=user, title='AAAA', text='AAAA Text',
                state=state, banner_id=1)
        idea.save()

        idea.tags.add('bbb', 'ccc', 'ddd')
        views.room_detail(mock_req(), slug='xxxx')
        context = render.call_args[0][2]
        self.assertTrue('tags' in context)
        self.assertEqual(3, len(context['tags']))
        self.assertEqual(set(['bbb', 'ccc', 'ddd']), 
                set([t.name for t in context['tags']]))

    @patch('idea.views.render')
    def test_private_tags_top_list(self, render):
        """
        Tag list should be in proper order.
        """
        user = random_user()
        state = models.State.objects.get(name='Active')
        state.save()

        # create a private and public banner
        self._generate_data(entry_data=None)

        #   Make 13 tags, and assign each to a set of ideas
        for count in range(30):
            tag = str(count)*4
            for i in range(count+1):
                idea = models.Idea(creator=user, title=str(i)*4, 
                        text=str(i)*4 +' Text', state=state, banner_id=1)
                idea.save()
                idea.tags.add(tag)

        views.room_detail(mock_req(), slug='xxxx')
        context = render.call_args[0][2]
        self.assertTrue('tags' in context)
        self.assertEqual(25, len(context['tags']))
        # 29292929, 28282828, 27272727, ...
        self.assertEqual([str(i)*4 for i in range(29,4,-1)],
                [t.name for t in context['tags']])

    @patch('idea.views.render')
    def test_private_tags_count(self, render):
        """
        Tag list should include tag count.
        """
        user = random_user()
        state = models.State.objects.get(name='Active')
        state.save()

        self._generate_data(entry_data=None)
 
        #   Make 13 tags, and assign each to a set of ideas
        for count in range(13):
            tag = str(count)*4
            for i in range(count+1):
                idea = models.Idea(creator=user, title=str(i)*4, 
                        text=str(i)*4 +' Text', state=state, banner_id=1)
                idea.save()
                idea.tags.add(tag)

        # create some dummy tags that are not part of this banner's ideas
        for count in range(2):
            tag = str(count)*4
            for i in range(count+1):
                idea = models.Idea(creator=user, title=str(i)*4+'2', 
                        text=str(i)*42 +' Text', state=state)
                idea.save()
                idea.tags.add(tag)
        banner = models.Banner(id=2, title="XXXX", text="text", is_private=True,
                               start_date=datetime.date.today())
        banner.save()
        for count in range(2):
            tag = str(count)*4
            for i in range(count+1):
                idea = models.Idea(creator=user, title=str(i)*4+'3', 
                        text=str(i)*4 +'3 Text', state=state, banner_id=2)
                idea.save()
                idea.tags.add(tag)
        banner = models.Banner(id=3, title="XXXX", text="text", is_private=True,
                               start_date=datetime.date.today())
        banner.save()
        for count in range(2):
            tag = str(count)*4
            for i in range(count+1):
                idea = models.Idea(creator=user, title=str(i)*4+'4', 
                        text=str(i)*4 +'4 Text', state=state, banner_id=3)
                idea.save()
                idea.tags.add(tag)

        views.room_detail(mock_req(), slug='xxxx')
        context = render.call_args[0][2]
        self.assertTrue('tags' in context)

        for i in range(12,2,-1):
            tag = context['tags'][12-i]
            self.assertTrue(hasattr(tag, 'count'))
            self.assertEqual(i+1, tag.count)

    @patch('idea.views.render')
    def test_private_tags_active(self, render):
        """
        Tag list should include if tag was active in this search.
        """
        def add_tag(idea, nonce):
            tag = str(nonce % 3)
            idea.tags.add(tag)
        self._generate_data(postfn=add_tag)

        views.room_detail(mock_req(), slug='xxxx')
        context = render.call_args[0][2]
        self.assertTrue('tags' in context)
        for tag in context['tags']:
            self.assertFalse(tag.active)

        views.room_detail(mock_req('/?tags=0'), slug='xxxx')
        context = render.call_args[0][2]
        for tag in context['tags']:
            self.assertEqual(tag.name == '0', tag.active)

        views.room_detail(mock_req('/?tags=1'), slug='xxxx')
        context = render.call_args[0][2]
        for tag in context['tags']:
            self.assertEqual(tag.name == '1', tag.active)

        views.room_detail(mock_req('/?tags=1,2'), slug='xxxx')
        context = render.call_args[0][2]
        for tag in context['tags']:
            self.assertEqual(tag.name in ['1','2'], tag.active)


    @patch('idea.views.render')
    def test_private_tag_filter(self, render):
        """
        List of ideas should be filterable by tag.
        """
        def add_tag(idea, nonce):
            #entry_data=[(5, 'AAAA'), (9, 'BBBB'), (3, 'CCCC'), (7, 'DDDD'),
            #            (1, 'EEEE'), (11, 'FFFF')]):
            tag = str(nonce % 3)  # results: 2 0 0 1 1 2
            idea.tags.add(tag)
            tag = str(nonce % 7)  # results: 5 2 3 0 1 4
            idea.tags.add(tag)
        self._generate_data(postfn=add_tag)

        views.room_detail(mock_req(), slug='xxxx')
        context = render.call_args[0][2]
        self.assertTrue('ideas' in context)
        self.assertEqual(6, len(context['ideas']))
        self.assertEqual(6, len(context['tags']))
        self.assertEqual(set(['0','1','2','3','4','5']),
                set([t.name for t in context['tags']]))

        views.room_detail(mock_req('/?tags=0'), slug='xxxx')
        context = render.call_args[0][2]
        self.assertEqual(3, len(context['ideas']))
        self.assertEqual(set(['BBBB', 'CCCC', 'DDDD']), 
                set([i.title for i in context['ideas']]))
        self.assertEqual(4, len(context['tags']))
        self.assertEqual(set(['0','1','2','3']),
                set([t.name for t in context['tags']]))

        views.room_detail(mock_req('/?tags=2'), slug='xxxx')
        context = render.call_args[0][2]
        self.assertEqual(3, len(context['ideas']))
        self.assertEqual(set(['AAAA', 'BBBB', 'FFFF']), 
                set([i.title for i in context['ideas']]))
        self.assertEqual(4, len(context['tags']))
        self.assertEqual(set(['0','2','4','5']),
                set([t.name for t in context['tags']]))

        views.room_detail(mock_req('/?tags=0,2'), slug='xxxx')
        context = render.call_args[0][2]
        self.assertEqual(1, len(context['ideas']))
        self.assertEqual(set(['BBBB']), 
                set([i.title for i in context['ideas']]))
        self.assertEqual(2, len(context['tags']))
        self.assertEqual(set(['0','2']),
                set([t.name for t in context['tags']]))

    @patch('idea.views.render')
    def test_private_banner_is_not_current(self, render):
        """
        Test boolean flag for banner status (active or not)
        """
        banner = models.Banner(id=1, title="xxxx", text="text", is_private=True,
                               start_date=datetime.date.today())
        banner.save()

        views.room_detail(mock_req(), slug='xxxx')
        context = render.call_args[0][2]
        self.assertTrue('is_current_banner' in context)
        self.assertFalse(context['is_current_banner'])
