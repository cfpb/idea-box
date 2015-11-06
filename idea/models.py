from datetime import datetime
from django.contrib.auth.models import SiteProfileNotAvailable
from django.conf import settings
from core.custom_comments.models import MPTTComment
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.timezone import get_default_timezone
from django.utils.translation import ugettext_lazy

if 'core.taggit' in settings.INSTALLED_APPS:
    from core.taggit.managers import TaggableManager
else:
    from taggit.managers import TaggableManager


def unique_slug(item, slug_source, slug_field):
    """
    Ensures a unique slug field by appending an integer counter to duplicate
    slugs.

    The item's slug field is first prepopulated by slugify-ing the source
    field. If that value already exists, a counter is appended to the slug,
    and the counter incremented upward until the value is unique.

    For instance, if you save an object titled Daily Roundup, and the slug
    daily-roundup is already taken, this function will try daily-roundup-2,
    daily-roundup-3, daily-roundup-4, etc, until a unique value is found.

    Call from within a model's custom save() method like so:
    unique_slug(item, slug_source='field1', slug_field='field2')
    where the value of field slug_source will be used to prepopulate the value
    of slug_field.
    """
    if not getattr(item, slug_field):  # if it already has slug, do nothing.
        from django.template.defaultfilters import slugify
        slug = slugify(getattr(item, slug_source))
        itemModel = item.__class__
        # the following gets all existing slug values
        allSlugs = [sl.values()[0]
                    for sl in itemModel.objects.values(slug_field)]
        if slug in allSlugs:
            import re
            counterFinder = re.compile(r'-\d+$')
            counter = 2
            slug = "%s-%i" % (slug, counter)
            while slug in allSlugs:
                slug = re.sub(counterFinder, "-%i" % counter, slug)
                counter += 1
        setattr(item, slug_field, slug)


class UserTrackable(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL)
    #   use a lambda so that this is evaluated upon creation (rather than
    #   once upon class import)
    time = models.DateTimeField(
        default=lambda: datetime.utcnow().replace(tzinfo=get_default_timezone()))

    class Meta:
        abstract = True


class Banner(models.Model):

    """ The banner text at the beginning of IdeaBox pages, asking the question.
    This can be used to run informal campaigns soliciting ideas around specific
    topics. """

    title = models.CharField(max_length=50)
    slug = models.SlugField(ugettext_lazy("Slug"), editable=False, unique=True, blank=True)
    text = models.TextField(max_length=2000, verbose_name="description")
    start_date = models.DateField(
        help_text="The date from which this banner will be displayed.")
    end_date = models.DateField(null=True, blank=True,
                                help_text="Empty indicates that the banner " +
                                "should be continued indefinitely. ")
    is_private = models.BooleanField('private room', default=False)
    is_votes = models.BooleanField('voting enabled', default=True)

    def save(self, *args, **kwargs):
        unique_slug(self, 'title', 'slug')
        super(Banner, self).save(*args, **kwargs)

    def __unicode__(self):
        if self.end_date:
            return u'%s (ends %s)' % (self.title, self.end_date)
        else:
            return u'%s' % self.title

    def room_url(self):
        return reverse('idea:room_detail', args=(self.slug,))

    def room_link(self):
        return "<a href='%s'>%s</a>" % (self.room_url(), self.title)


class State(models.Model):

    """ The state an idea goes through. """
    name = models.CharField(max_length=50)

    # States are ordered with respect to each other.
    # The first State has no previous.
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
            'recent_activity': """
                SELECT MAX(CASE WHEN COALESCE(c.time, date('2001-01-01')) >= COALESCE(b.submit_date, date('2001-01-01')) AND COALESCE(c.time, date('2001-01-01')) >= a.time THEN c.time
                                WHEN COALESCE(b.submit_date, date('2001-01-01')) >= a.time THEN b.submit_date
                                ELSE a.time
                           END)
                FROM idea_idea a
                LEFT OUTER JOIN django_comments b ON a.id = b.object_pk
                LEFT OUTER JOIN idea_vote c ON a.id = c.idea_id
                WHERE a.id = idea_idea.id
            """,
            #   Don't use annotate() as it conflicts with extra()
            'vote_count': """
                SELECT count(*) FROM idea_vote WHERE idea_id = idea_idea.id
            """
        }, select_params=[idea_type.id])


class Idea(UserTrackable):
    title = models.CharField(max_length=50, blank=False, null=False,
                             help_text="""
        Make your idea stand out from the rest with a good title.""")
    summary = models.TextField(max_length=200, help_text="""
        Get people's attention and instant support! Only the first 200
        characters make it onto the IdeaBox landing page.""")
    text = models.TextField(max_length=2000, null=False,
                            verbose_name="detail", help_text="""
        Describe your reasoning to garner deeper support. Include links to
        any research, pages, or even other ideas.""")
    banner = models.ForeignKey(
        Banner, verbose_name="challenge", blank=True, null=True)
    state = models.ForeignKey(State)

    tags = TaggableManager(blank=False, help_text="""
        Make it easy for supporters to find your idea.  See how many other
        ideas have the same tags for potential collaboration or a little
        healthy competition.""")
    voters = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                    through="Vote", null=True,
                                    related_name="idea_vote_creator")
    is_anonymous = models.BooleanField("anonymous Idea", default=False, help_text="""
        Only enable anonymous if the Idea's challenge is private""")

    def __unicode__(self):
        return u'%s' % self.title

    def url(self):
        """
        Lookup the view url for this idea.
        """
        return reverse('idea:idea_detail', args=(self.id,))

    @property
    def comments(self):
        return MPTTComment.objects.for_model(self.__class__).filter(
            is_public=True, is_removed=False, object_pk=self.pk)

    @property
    def members(self):
        """
        Return all users participating in an idea
        """
        members = []
        members.append(self.creator)

        for c in self.comments:
            if c.user not in members and not c.is_anonymous:
                members.append(c.user)

        return members

    def get_creator_profile(self):
        if self.is_anonymous:
            return None
        else:
            try:
                return self.creator.get_profile()
            except (ObjectDoesNotExist, SiteProfileNotAvailable):
                return None

    objects = IdeaManager()

# We can only upvote.
UP_VOTE = 1
VOTE_CHOICES = ((u'+1', UP_VOTE),)


class Vote(UserTrackable):
    vote = models.SmallIntegerField(choices=VOTE_CHOICES, default=1)
    idea = models.ForeignKey(Idea)


class Config(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField(max_length=2000)
