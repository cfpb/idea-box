from haystack import indexes
from models import Idea, Banner
from django.core.urlresolvers import reverse
from time import mktime, strptime

class IdeaIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    display = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr="summary", null=True)
    index_name = indexes.CharField(indexed=False)
    index_priority = indexes.IntegerField(indexed=False)
#  TODO causes all tests to fail
#    index_sort = indexes.IntegerField(indexed=False, null=True)
    url = indexes.CharField(indexed=False, null=True)

    PRIORITY = 4

    def prepare_index_name(self, obj):
        return "Ideas"

    def prepare_index_priority(self, obj):
        return self.PRIORITY

    def prepare_index_sort(self, obj):
        # want a positive number so banner results appear above/before ideas
        #9999999999 =~ year 2286
        return 9999999999 - int(mktime(strptime(obj.recent_activity, "%Y-%m-%d %H:%M:%S")))

    def prepare_url(self, obj):
        return reverse('idea:idea_detail', args=(obj.id,))

    def get_model(self):
        return Idea

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        # State 2 = Archived
        return self.get_model().objects.related_with_counts().exclude(state=2).exclude(banner__is_private=True)


class BannerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    display = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr="text")
    index_name = indexes.CharField(indexed=False)
    index_priority = indexes.IntegerField(indexed=False)
    index_sort = indexes.IntegerField(indexed=False, null=True)
    url = indexes.CharField(indexed=False, null=True)

    PRIORITY = 4

    def prepare_index_name(self, obj):
        return "Ideas"

    def prepare_index_priority(self, obj):
        return self.PRIORITY

    def prepare_index_sort(self, obj):
        return 0 - int(mktime(obj.start_date.timetuple()))

    def prepare_url(self, obj):
        return reverse('idea:challenge_detail', args=(obj.id,))

    def prepare_display(self, obj):
        return "Challenge: " + obj.title

    def get_model(self):
        return Banner

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.exclude(is_private=True)
