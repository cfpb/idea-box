from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import unittest
from haystack import connections
from idea import models, views
from idea.tests.utils import random_user

class SearchTest(TestCase):
    fixtures = ['state']
    backend = connections['default'].get_backend()
    backend_type = connections['default'].backend.__name__

    def setUp(self):
        self.backend.clear()

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
