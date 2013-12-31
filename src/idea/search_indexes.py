from haystack import indexes
from models import Idea

class IdeaIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True,
                template_name='idea/index/idea_text.txt')

    def index_queryset(self, using=None):
        return Idea.objects.related_with_counts()

    def get_model(self):
        return Idea
