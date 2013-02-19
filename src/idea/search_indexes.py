from haystack.indexes import *
from haystack import site
from models import Idea

class IdeaIndex(RealTimeSearchIndex):
    text = CharField(document=True, use_template=True, 
            template_name='idea/index/idea_text.txt')
   
    def index_queryset(self):
        return Idea.objects.related_with_counts()

site.register(Idea, IdeaIndex)

