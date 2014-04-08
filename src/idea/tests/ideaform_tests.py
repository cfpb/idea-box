from django.test import TestCase
from idea.forms import IdeaForm

class IdeaTests(TestCase):

    def test_idea_all_fields(self):
        f = IdeaForm({
            'title':'Create an automatic birthday greeting emailer.',
            'summary': 'test summary',
            'text': 'test text',
            'tags': 'test, tags',
        })
        self.assertEqual(f.is_valid(), True)

    def test_idea_title_required(self):
        """
            The field 'title' is required when adding an idea.
        """
        f = IdeaForm({
            'summary': 'test summary',
            'text': 'test text',
            'tags': 'test, tags',
        })
        self.assertEqual(f.is_valid(), False)

    def test_idea_summary_required(self):
        """
            The field 'summary' is required when adding an idea. 
        """
        f = IdeaForm({
            'title':'Create an automatic birthday greeting emailer.',
            'text': 'test text',
            'tags': 'test, tags',
        })
        self.assertEqual(f.is_valid(), False)

    def test_idea_text_required(self):
        """
            The field 'text' is option when adding an idea. 
        """
        f = IdeaForm({
            'title':'Create an automatic birthday greeting emailer.',
            'summary': 'test summary',
            'tags': 'test, tags',
        })
        self.assertEqual(f.is_valid(), False)

    def test_idea_tags_required(self):
        """
            The field 'text' is option when adding an idea. 
        """
        f = IdeaForm({
            'title':'Create an automatic birthday greeting emailer.',
            'summary': 'test summary',
            'text': 'test text',
        })
        self.assertEqual(f.is_valid(), False)
