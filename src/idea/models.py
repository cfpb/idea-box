from datetime import datetime
from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.contrib.comments import Comment
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.timezone import get_default_timezone
from core.taggit.managers import TaggableManager

class UserTrackable(models.Model):
    creator = models.ForeignKey(User)
    #   use a lambda so that this is evaluated upon creation (rather than
    #   once upon class import)
    time = models.DateTimeField(default =
            lambda:datetime.utcnow().replace(tzinfo=get_default_timezone()))

    class Meta:
        abstract = True
  
class Banner(models.Model):
    """ The banner text at the beginning of IdeaBox pages, asking the question. 
    This can be used to run informal campaigns soliciting ideas around specific 
    topics. """

    text = models.CharField(max_length=512)
    start_date = models.DateField(help_text="The date from which this banner will be displayed.")
    end_date =  models.DateField(null=True, blank=True,  
               help_text="Empty indicates that the banner should be continued indefinitely. ")

    def __unicode__(self):
        return u'%s (%s to %s)' % (self.text, self.start_date, self.end_date)

class State(models.Model):
    """ The state an idea goes through. """
    name = models.CharField(max_length=50)

    #States are ordered with respect to each other. 
    #The first State has no previous. 
    previous = models.OneToOneField('self', null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

class IdeaManager(models.Manager):
    def related_with_counts(self):
        idea_type = ContentType.objects.get(app_label="idea", model="idea")
        return self.select_related().extra(select={
            'comment_count': """
                SELECT count(*) FROM django_comments 
                WHERE django_comments.content_type_id = %s
                AND django_comments.object_pk = idea_idea.id
            """,
            #   Don't use annotate() as it conflicts with extra()
            'vote_count': """
                SELECT count(*) FROM idea_vote WHERE idea_id = idea_idea.id
            """
            }, select_params=[idea_type.id])

class Idea(UserTrackable):
    title = models.CharField(max_length=140, blank=False, null=False)
    text = models.TextField(blank=True, null=True)
    state = models.ForeignKey(State)

    tags = TaggableManager(blank=True)

    def __unicode__(self):
        return u'%s' % self.title

    def url(self):
        """
        Lookup the view url for this idea.
        """
        return reverse('idea.views.detail', args=(self.id,))

    def get_creator_profile(self):
        try:
            return self.creator.get_profile()
        except (ObjectDoesNotExist, SiteProfileNotAvailable): 
            return None

    objects = IdeaManager()

#We can only upvote. 
UP_VOTE = 1
VOTE_CHOICES = ((u'+1', UP_VOTE),)

class Vote(UserTrackable):
    vote = models.SmallIntegerField(choices=VOTE_CHOICES, default=1) 
    idea = models.ForeignKey(Idea)
