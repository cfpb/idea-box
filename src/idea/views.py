from datetime import date
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import SiteProfileNotAvailable, User
from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from idea.forms import IdeaForm, IdeaTagForm, UpVoteForm
from idea.models import Idea, State, Vote, Banner
from idea.utility import state_helper
from idea.models import UP_VOTE

try:
    from core.taggit.models import Tag, TaggedItem
    from core.taggit.utils import add_tags
    COLLAB_TAGS = True;
except ImportError:
    from taggit.models import Tag
    COLLAB_TAGS = False;

from haystack import connections


def _render(req, template_name, context={}):
    context['active_app'] = 'Idea'
    context['app_link'] = reverse('idea:idea_list')
    return render(req, template_name, context)


def get_current_banners():
    return Banner.objects.filter(start_date__lte=date.today()).exclude(end_date__lt=date.today())


def get_banner():
    today = date.today()
    timed_banners = Banner.objects.filter(start_date__lte=today,
                                          end_date__isnull=False,
                                          end_date__gt=today)

    if timed_banners:
        return timed_banners[0]
    else:
        indefinite_banners = Banner.objects.filter(start_date__lte=today,
                                                   end_date__isnull=True)
        if indefinite_banners:
            return indefinite_banners[0]
        else:
            return None


@login_required
def list(request, sort_or_state=None):
    tag_strs = request.GET.get('tags', '').split(',')
    tag_strs = [t for t in tag_strs if t != u'']
    tag_ids = [tag.id for tag in Tag.objects.filter(slug__in=tag_strs)]
    page_num = request.GET.get('page_num')

    ideas = Idea.objects.related_with_counts()

    #   Tag Filter
    if tag_ids:
        ideas = ideas.filter(tags__pk__in=tag_ids).distinct()

    #   URL Filter - either archive or one of the sorts
    if sort_or_state == 'archived':
        ideas = ideas.filter(state=State.objects.get(name='Archive')
                             ).order_by('-vote_count')
    else:
        ideas = ideas.filter(state=State.objects.get(name='Active'))
        if sort_or_state == 'vote':
            ideas = ideas.order_by('-vote_count')
        elif sort_or_state == 'recent':
            ideas = ideas.order_by('-time')
        else:
            sort_or_state = 'trending'
            ideas = ideas.order_by('-recent_activity')

    IDEAS_PER_PAGE = getattr(settings, 'IDEAS_PER_PAGE', 10)
    pager = Paginator(ideas, IDEAS_PER_PAGE)
    #   Boiler plate paging -- @todo abstract this
    try:
        page = pager.page(page_num)
    except PageNotAnInteger:
        page = pager.page(1)
    except EmptyPage:
        page = pager.page(pager.num_pages)

    #   List of tags
    tags = Tag.objects.filter(
        taggit_taggeditem_items__content_type__name='idea'
    ).annotate(count=Count('taggit_taggeditem_items')
               ).order_by('-count', 'name')[:10]

    for tag in tags:
        if tag.slug in tag_strs:
            tag_slugs = ",".join([s for s in tag_strs if s != tag.slug])
        else:
            tag_slugs = ",".join(tag_strs + [tag.slug])
        #   Minor tweak: Links just turn on/off a single tag
        if tag.slug in tag_strs:
            tag.tag_url = "%s" % (reverse('idea:idea_list',
                                          args=(sort_or_state,)))
            tag.active = True
        else:
            tag.tag_url = "%s?tags=%s" % (reverse('idea:idea_list',
                                                  args=(sort_or_state,)),
                                          tag.slug)
            tag.active = False

    banner = get_banner()

    return _render(request, 'idea/list.html', {
        'sort_or_state': sort_or_state,
        'ideas':    page,
        'tags':     tags,  # list of popular tags
        'banner': banner,
    })


def vote_up(idea, user):
    vote = Vote()
    vote.idea = idea
    vote.creator = user
    vote.save()


@require_POST
@login_required
def up_vote(request):
    form = UpVoteForm(request.POST)

    if form.is_valid():
        idea_id = form.cleaned_data['idea_id']
        next_url = form.cleaned_data['next']

        idea = Idea.objects.get(pk=idea_id)

        # Up voting is idempotent
        existing_votes = Vote.objects.filter(
            idea=idea, creator=request.user, vote=UP_VOTE)

        if not existing_votes.exists():
            vote_up(idea, request.user)

        return HttpResponseRedirect(next_url)


def more_like_text(text, klass):
    """
    Return more entries like the provided chunk of text. We have to jump
    through some hoops to get this working as the haystack API does not
    account for this case. In particular, this is a solr-specific hack.
    """
    back = connections['default'].get_backend()

    if hasattr(back, 'conn'):
        query = {'query': {
            'filtered': {
                'query': {
                    'fuzzy_like_this': {
                        'like_text': text
                    }
                },
                'filter': {
                    'bool': {
                        'must': {
                            'term': {'django_ct': 'idea.idea'}
                        }
                    }
                }
            }
        }

        }
        results = back.conn.search(query)
        return back._process_results(results)['results']
    else:
        return []


@login_required
def detail(request, idea_id):
    """
    Detail view; idea_id must be a string containing an int.
    """
    idea = get_object_or_404(Idea, pk=int(idea_id))
    if request.method == 'POST':
        tag_form = IdeaTagForm(request.POST)
        if tag_form.is_valid():
            data = tag_form.clean()['tags']
            tags = [tag.strip() for tag in data.split(',')
                    if tag.strip() != '']
            try:
                for t in tags:
                    add_tags(idea, t, None, request.user, 'idea')
            except NameError:  # catch if add_tags doesn't exist
                idea.tags.add(*tags)
            return HttpResponseRedirect(
                reverse('idea:idea_detail', args=(idea.id,)))
    else:
        tag_form = IdeaTagForm()

    voters = idea.voters.all()

    for v in voters:
        try:
            v.profile = v.get_profile()
        except (ObjectDoesNotExist, SiteProfileNotAvailable):
            v.profile = None

    idea_type = ContentType.objects.get(app_label="idea", model="idea")

    tags = idea.tags.extra(select={
        'tag_count': """
            SELECT COUNT(*) from taggit_taggeditem tt
            WHERE tt.tag_id = taggit_tag.id 
            AND content_type_id = %s 
        """
    }, select_params=[idea_type.id]).order_by('name')

    tags_created_by_user = []
    if COLLAB_TAGS:
        for tag in tags:
            tag.tag_url = "%s?tags=%s" % (reverse('idea:idea_list'), tag.slug)
            for ti in tag.taggit_taggeditem_items.all():
                if ti.tag_creator == request.user and \
                   ti.content_type.name == "idea":
                    tags_created_by_user.append(tag.name)

    return _render(request, 'idea/detail.html', {
        'idea': idea,  # title, body, user name, user photo, time
        'support': request.user in voters,
        'tags': tags,
        'tags_created_by_user': tags_created_by_user,
        'voters': voters,
        'tag_form': tag_form
    })


@login_required
def add_idea(request):
    if request.method == 'POST':
        idea = Idea(creator=request.user, state=state_helper.get_first_state())
        if idea.state.name == 'Active':
            form = IdeaForm(request.POST, instance=idea)
            if form.is_valid():
                new_idea = form.save()
                vote_up(new_idea, request.user)
                return HttpResponseRedirect(reverse('idea:idea_detail',
                                                    args=(idea.id,)))
            else:
                form.fields["banner"].queryset = get_current_banners()
                return _render(request, 'idea/add.html', {'form': form, })
        else:
            return HttpResponse('Idea is archived', status=403)
    else:
        idea_title = request.GET.get('idea_title', '')
        form = IdeaForm(initial={'title': idea_title})
        form.fields["banner"].queryset = get_current_banners()
        return _render(request, 'idea/add.html', {
            'form': form,
            'similar': [r.object for r in more_like_text(idea_title, Idea)]
        })


@login_required
def banner_detail(request, banner_id):
    """
    Banner detail view; banner_id must be a string containing an int.
    """
    banner = Banner.objects.get(id=banner_id)

    tag_strs = request.GET.get('tags', '').split(',')
    tag_strs = [t for t in tag_strs if t != u'']
    tag_ids = [tag.id for tag in Tag.objects.filter(slug__in=tag_strs)]
    page_num = request.GET.get('page_num')

    ideas = Idea.objects.related_with_counts().filter(banner=banner)

    #   Tag Filter
    if tag_ids:
        ideas = ideas.filter(tags__pk__in=tag_ids).distinct()

    IDEAS_PER_PAGE = getattr(settings, 'IDEAS_PER_PAGE', 10)
    pager = Paginator(ideas, IDEAS_PER_PAGE)
    #   Boiler plate paging -- @todo abstract this
    try:
        page = pager.page(page_num)
    except PageNotAnInteger:
        page = pager.page(1)
    except EmptyPage:
        page = pager.page(pager.num_pages)

    #   List of tags that are associated with an idea in the banner list
    banner_ideas = Idea.objects.filter(banner=banner)
    banner_tags = Tag.objects.filter(
        taggit_taggeditem_items__content_type__name='idea',
        taggit_taggeditem_items__object_id__in=banner_ideas)
    tags = banner_tags.filter(
        taggit_taggeditem_items__content_type__name='idea'
    ).annotate(count=Count('taggit_taggeditem_items')
               ).order_by('-count', 'name')[:10]

    for tag in tags:
        if tag.slug in tag_strs:
            tag_slugs = ",".join([s for s in tag_strs if s != tag.slug])
        else:
            tag_slugs = ",".join(tag_strs + [tag.slug])
        #   Minor tweak: Links just turn on/off a single tag
        if tag.slug in tag_strs:
            tag.tag_url = "%s" % (reverse('idea:banner_detail',
                                          args=(banner_id,)))
            tag.active = True
        else:
            tag.tag_url = "%s?tags=%s" % (reverse('idea:banner_detail',
                                                  args=(banner_id,)),
                                          tag.slug)
            tag.active = False

    return _render(request, 'idea/banner_detail.html', {
        'ideas':    page,
        'tags':     tags,  # list of tags associated with banner ideas
        'banner': banner,
    })

@login_required
def remove_tag(request, idea_id, tag_slug):
    idea = Idea.objects.get(pk=idea_id)
    tag = Tag.objects.get(slug=tag_slug)
    try:
        taggeditem = TaggedItem.objects.get(tag_creator=request.user,
                                            object_id=idea.id, tag=tag)
        taggeditem.delete()
    except TaggedItem.DoesNotExist:  # catch if object not found
        pass
    except NameError:  # catch if TaggedItem doesn't exist
        pass
    return HttpResponseRedirect(reverse('idea:idea_detail', args=(idea.id,)))

