import datetime
from django.test import TestCase
from idea import models, views

def get_relative_date(delta_days=0):
    return datetime.date.today() + datetime.timedelta(days=delta_days)

class BannerTest(TestCase):
    def test_timebound_banner(self):
        yesterday = get_relative_date(-1)
        tomorrow = get_relative_date(+1)
        banner = models.Banner(title="How would you improve our vacation policy?",
                text="We would like to know what we can do to improve your work/life balance",
                start_date=yesterday, end_date=tomorrow)
        banner.save()

        b = views.get_banner()
        self.assertIsNotNone(b)

    def test_indefinite_banner(self):
        yesterday = get_relative_date(-1)
        banner = models.Banner(title="How would you improve our vacation policy?", 
                text="We would like to know what we can do to improve your work/life balance",
                start_date=yesterday)
        banner.save()

        b = views.get_banner()
        self.assertIsNotNone(b)
        self.assertEquals(b.title, "How would you improve our vacation policy?")
        self.assertEquals(b.text, "We would like to know what we can do to improve your work/life balance")

    def test_timed_before_indefinite(self):
        yesterday = get_relative_date(-1)
        tomorrow = get_relative_date(+1)

        timed_banner = models.Banner(title="How would you improve our vacation policy?", 
                text="We would like to know what we can do to improve your work/life balance",
                start_date=yesterday, end_date=tomorrow)
        timed_banner.save()

        banner = models.Banner(title="How would you improve our promotion process?", 
                text="We would like to know what we can do to improve your work/life balance",
                start_date=yesterday)
        banner.save()

        b = views.get_banner()
        self.assertIsNotNone(b)
        self.assertEquals(b.title, "How would you improve our vacation policy?")
        self.assertEquals(b.text, "We would like to know what we can do to improve your work/life balance")

    def test_no_banner(self):
        b = views.get_banner()
        self.assertIsNone(b)

    def test_outside_timed(self):
        tomorrow = get_relative_date(+1)
        end = get_relative_date(+5)
        banner = models.Banner(title="How would you improve our vacation policy?", 
                text="We would like to know what we can do to improve your work/life balance",
                start_date=tomorrow, end_date=end)
        banner.save()
        b = views.get_banner()
        self.assertIsNone(b)

    def test_get_current_banners(self):
        # Banners should be ordered by end date, nearest end date first
        yesterday = get_relative_date(-1)
        today = datetime.date.today()
        tomorrow = get_relative_date(+1)
        self.assertEqual(views.get_current_banners().count(), 0)
        banner1 = models.Banner(title="How would you improve our vacation policy?", 
                text="We would like to know what we can do to improve your work/life balance",
                start_date=yesterday, end_date=today)
        banner1.save()
        self.assertEqual(list(views.get_current_banners()), [banner1])
        banner2 = models.Banner(title="How would you improve our vacation policy?", 
                text="We would like to know what we can do to improve your work/life balance",
                start_date=today)
        banner2.save()
        self.assertEqual(list(views.get_current_banners()), [banner1,banner2])
        banner3 = models.Banner(title="How would you improve our vacation policy?", 
                text="We would like to know what we can do to improve your work/life balance",
                start_date=yesterday, end_date=yesterday)
        banner3.save()
        self.assertEqual(list(views.get_current_banners()), [banner1,banner2])
        banner4 = models.Banner(title="How would you improve our vacation policy?", 
                text="We would like to know what we can do to improve your work/life balance",
                start_date=tomorrow, end_date=tomorrow)
        banner4.save()
        self.assertEqual(list(views.get_current_banners()), [banner1,banner2])
        banner5 = models.Banner(title="How would you improve our vacation policy?", 
                text="We would like to know what we can do to improve your work/life balance",
                start_date=today, end_date=tomorrow)
        banner5.save()
        self.assertEqual(list(views.get_current_banners()), [banner1,banner5,banner2])
