from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import unittest
from haystack import connections
from idea import models, views
from idea.tests.utils import random_user
from datetime import date

class SearchTest(TestCase):
    fixtures = ['state']
    backend = connections['default'].get_backend()
    backend_type = connections['default'].backend.__name__

    @unittest.skipIf(backend_type == 'SimpleSearchBackend', 
            "Simple backend doesn't allow itself to be cleared")
    def setUp(self):
        self.backend.clear()

    @unittest.skipIf(backend_type == 'SimpleSearchBackend', 
            "See https://github.com/toastdriven/django-haystack/issues/908")
    def test_add_idea_title(self):
        """
        Check that adding a new idea allows title to be immediately
        searchable.
        """
        req = RequestFactory().post('/', {'title': 'example_title'})
        req.user = random_user()
        views.add_idea(req)
        results = self.backend.search('example_title')
        self.assertEqual(1, results['hits'])

    @unittest.skipIf(backend_type == 'SimpleSearchBackend', 
            "See https://github.com/toastdriven/django-haystack/issues/908")
    def test_add_idea_summary(self):
        """
        Check that adding a new idea allows title to be immediately
        searchable.
        """
        req = RequestFactory().post('/', {
            'title':'test title',
            'summary': 'example_summary',
            'text': 'test text',
            'tags': 'test, tags'
        })
        req.user = random_user()
        views.add_idea(req)
        results = self.backend.search('example_summary')
        self.assertEqual(1, results['hits'])

    @unittest.skipIf(backend_type == 'SimpleSearchBackend', 
            "See https://github.com/toastdriven/django-haystack/issues/908")
    def test_add_idea_text(self):
        """
        Check that adding a new idea allows title to be immediately
        searchable.
        """
        req = RequestFactory().post('/', {
            'title':'test title',
            'summary': 'test summary',
            'text': 'example_text',
            'tags': 'test, tags'
        })
        req.user = random_user()
        views.add_idea(req)
        results = self.backend.search('example_text')
        self.assertEqual(1, results['hits'])

    @unittest.skipIf(backend_type == 'SimpleSearchBackend', 
            "Simple backend doesn't handle tags")
    def test_add_idea_tag(self):
        """
        Check that adding a new idea allows the associated tag to be
        immediately searchable.
        """
        req = RequestFactory().post('/', 
            {'title': 'title', 'tags': 'example_tag'})
        req.user = random_user()
        views.add_idea(req)
        results = self.backend.search('example_tag')
        self.assertEqual(1, results['hits'])

    @unittest.skipIf(backend_type == 'SimpleSearchBackend', 
        "Simple backend doesn't handle tags")
    def test_edit_idea_tag(self):
        """
        Check that adding a new idea allows the associated tag to be
        immediately searchable.
        """
        idea = models.Idea(creator=random_user(), title='title',
                state = models.State.objects.get(name='Active'))
        idea.save()
        results = self.backend.search('example_tag')
        self.assertEqual(0, results['hits'])

        req = RequestFactory().post('/', {'tags': 'example_tag'})
        req.user = random_user()
        views.detail(req, str(idea.id))
        results = self.backend.search('example_tag')
        self.assertEqual(1, results['hits'])

    @unittest.skipIf(backend_type == 'SimpleSearchBackend', 
            "See https://github.com/toastdriven/django-haystack/issues/908")
    def test_banner_title(self):
        """
        Check that adding a new idea allows title to be immediately
        searchable.
        """
        banner = models.Banner()
        banner.title = "example_title"
        banner.text = "test text"
        banner.start_date = date.today()
        banner.save()
        results = self.backend.search('example_title')
        self.assertEqual(1, results['hits'])

    @unittest.skipIf(backend_type == 'SimpleSearchBackend', 
            "See https://github.com/toastdriven/django-haystack/issues/908")
    def test_banner_text(self):
        """
        Check that adding a new idea allows title to be immediately
        searchable.
        """
        banner = models.Banner()
        banner.title = "test title"
        banner.text = "example_text"
        banner.start_date = date.today()
        banner.save()
        results = self.backend.search('example_text')
        self.assertEqual(1, results['hits'])
