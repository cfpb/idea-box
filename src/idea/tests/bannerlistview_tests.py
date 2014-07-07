from django.test import TestCase
from idea import models, views
from idea.tests.utils import mock_req
from mock import patch
import datetime

def get_relative_date(delta_days=0):
    return datetime.date.today() + datetime.timedelta(days=delta_days)

class ListViewTest(TestCase):
    """
    Tests for idea.views.list
    """
    fixtures = ['state']
    def _generate_data(self, paramfn=lambda x,y:None, postfn=lambda x,y:None,
            entry_data=[(5, 'AAAA'), (9, 'BBBB'), (3, 'CCCC'), (7, 'DDDD'),
                        (1, 'EEEE'), (11, 'FFFF')]):
        """
        Helper function to handle the banner creation.
        """

        def make_banner(nonce, title):
            kwargs = {'title': title, 'text': title + ' Text'}
            paramfn(kwargs, nonce)
            banner = models.Banner(**kwargs)
            banner.save()
            postfn(banner, nonce)
            return banner

        banner = [make_banner(pair[0], pair[1]) for pair in entry_data]

    @patch('idea.views.render')
    def test_banner_list(self, render):
        """
        Verify that the banner list works.
        """
        def add_dates(kwargs, nonce):
            baseline_start = -7
            baseline_end = -5
            # -2 0
            # 2 None
            # -4 None
            # 0 2
            # -6 -4
            # 4 6
            kwargs['start_date'] = get_relative_date(baseline_start + nonce)
            if nonce % 3 == 0:
                kwargs['end_date'] = None
            else:
                kwargs['end_date'] = get_relative_date(baseline_end + nonce)
        self._generate_data(paramfn=add_dates)
        views.banner_list(mock_req())

        context = render.call_args[0][2]
        self.assertTrue('current_banners' in context)
        self.assertTrue('past_banners' in context)
        self.assertEqual(3, len(context['current_banners']))
        self.assertEqual(1, len(context['past_banners']))
        self.assertEqual('AAAA', context['current_banners'][0].title)
        self.assertEqual('DDDD', context['current_banners'][1].title)
        self.assertEqual('CCCC', context['current_banners'][2].title)
        self.assertEqual('EEEE', context['past_banners'][0].title)
