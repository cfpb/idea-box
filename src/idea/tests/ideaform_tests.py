from django.test import TestCase
from idea.forms import IdeaForm

class IdeaTests(TestCase):
    def test_idea_title_required(self):
        """
            The field 'title' is required when adding an idea.
        """
        f = IdeaForm({'text':'Every employee should get 4 weeks of vacation.'})
        self.assertEqual(f.is_valid(), False)

    def test_idea_text_optional(self):
        """
            The field 'text' is option when adding an idea. 
        """
        f = IdeaForm({'title':'Create an automatic birthday greeting emailer.'})
        self.assertEqual(f.is_valid(), True)
