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
from django.db.models import Q

from idea.forms import IdeaForm, IdeaTagForm, UpVoteForm
from idea.models import Idea, State, Vote, Banner, Config
from idea.utility import state_helper
from idea.models import UP_VOTE

try:
    from core.taggit.models import Tag, TaggedItem
    from core.taggit.utils import add_tags
    COLLAB_TAGS = True
except ImportError:
    from taggit.models import Tag
    COLLAB_TAGS = False

from haystack import connections


def _render(req, template_name, context={}):
    context['active_app'] = 'Idea'
    context['is_idea'] = True
    context['app_link'] = reverse('idea:idea_list')
    return render(req, template_name, context)


def get_current_banners(additional_ids_list=None):
    start_date = Q(start_date__lte=date.today())
    end_date = Q(end_date__gte=date.today())|Q(end_date__isnull=True)
    banner_filter = (start_date&end_date)
    if additional_ids_list:
        banner_filter = banner_filter|Q(id__in=additional_ids_list)
    return Banner.objects.filter(banner_filter)


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
    for tag_id in tag_ids:
        ideas = ideas.filter(tags__pk=tag_id)

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
        taggit_taggeditem_items__content_type__name='idea',
        taggit_taggeditem_items__object_id__in=ideas
    ).annotate(count=Count('taggit_taggeditem_items')
               ).order_by('-count', 'name')[:25]

    for tag in tags:
        if tag.slug in tag_strs:
            tag_slugs = ",".join([s for s in tag_strs if s != tag.slug])
            tag.active = True
        else:
            tag_slugs = ",".join(tag_strs + [tag.slug])
            tag.active = False
        if tag_strs == [tag.slug]:
            tag.tag_url = "%s" % (reverse('idea:idea_list',
                                          args=(sort_or_state,)))
        else:
            tag.tag_url = "%s?tags=%s" % (reverse('idea:idea_list',
                                                  args=(sort_or_state,)),
                                          tag_slugs)

    banner = get_banner()
    try:
        about_text = Config.objects.get(key="list_about").value
    except Config.DoesNotExist:
        about_text = ""

    return _render(request, 'idea/list.html', {
        'sort_or_state': sort_or_state,
        'ideas': page,
        'tags': tags,  # list of popular tags
        'banner': banner,
        'about_text': about_text,
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
            for ti in tag.taggit_taggeditem_items.filter(tag_creator=request.user,
                                                         content_type__name="idea",
                                                         object_id=idea_id):
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
def add_idea(request, banner_id=None):
    if request.method == 'POST':
        matching_ideas = Idea.objects.filter(
            creator=request.user,
            title=request.POST.get('title', ''))
        if matching_ideas.count() > 0:
            # user already submitted this idea
            return HttpResponseRedirect(reverse('idea:idea_detail',
                                                args=(matching_ideas[0].id,)))
        idea = Idea(creator=request.user, state=state_helper.get_first_state())
        if idea.state.name == 'Active':
            form = IdeaForm(request.POST, instance=idea)
            if form.is_valid():
                new_idea = form.save()
                vote_up(new_idea, request.user)
                return _render(request, 'idea/add_success.html',
                               {'idea': new_idea, })
            else:
                if 'banner' in request.POST:
                    form.fields["banner"].queryset = get_current_banners()
                else:
                    form.fields.pop('banner')
                    form.fields.pop('challenge-checkbox')
                form.set_error_css()
                return _render(request, 'idea/add.html', {'form': form, })
        else:
            return HttpResponse('Idea is archived', status=403)
    else:
        idea_title = request.GET.get('idea_title', '')
        current_banners = get_current_banners()
        if current_banners.count() == 0:
            form = IdeaForm(initial={'title': idea_title})
            form.fields.pop('banner')
            form.fields.pop('challenge-checkbox')
        else:
            if banner_id and Banner.objects.get(id=banner_id) in get_current_banners():
                banner = Banner.objects.get(id=banner_id)
            else:
                banner = None
            form = IdeaForm(initial={'title': idea_title, 'banner': banner})
            form.fields["banner"].queryset = current_banners
        return _render(request, 'idea/add.html', {
            'form': form,
            'similar': [r.object for r in more_like_text(idea_title, Idea)]
        })


@login_required
def edit_idea(request, idea_id):
    idea = get_object_or_404(Idea, pk=int(idea_id))
    original_banner = idea.banner
    if idea.creator != request.user:
        return HttpResponseRedirect(reverse('idea:idea_detail',
                                            args=(idea_id,)))
    
    if request.method == 'POST':
        form = IdeaForm(request.POST, instance=idea)
        form.fields.pop('tags')
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('idea:idea_detail',
                                                args=(idea_id,)))
        else:
            if 'banner' in request.POST:
                if original_banner:
                    current_banners = get_current_banners([original_banner.id])
                else:
                    current_banners = get_current_banners()
                form.fields["banner"].queryset = current_banners
            else:
                form.fields.pop('banner')
                form.fields.pop('challenge-checkbox')
            form.set_error_css()
            return _render(request, 'idea/edit.html', {'form': form, 'idea': idea })
    else:
        form_initial = {}
        if original_banner:
            current_banners = get_current_banners([original_banner.id])
            form_initial["challenge-checkbox"] = "on"
        else:
            current_banners = get_current_banners()
        form = IdeaForm(instance=idea, initial=form_initial)
        form.fields.pop('tags')
        if len(current_banners) == 0:
            form.fields.pop('banner')
            form.fields.pop('challenge-checkbox')
        else:
            form.fields["banner"].queryset = current_banners
        return _render(request, 'idea/edit.html',
                       {'form': form, 'idea': idea })


@login_required
def banner_detail(request, banner_id):
    """
    Banner detail view; banner_id must be a string containing an int.
    """
    banner = Banner.objects.get(id=banner_id)
    is_current_banner = True if banner in get_current_banners() else False

    tag_strs = request.GET.get('tags', '').split(',')
    tag_strs = [t for t in tag_strs if t != u'']
    tag_ids = [tag.id for tag in Tag.objects.filter(slug__in=tag_strs)]
    page_num = request.GET.get('page_num')

    ideas = Idea.objects.related_with_counts().filter(
        banner=banner,
        state=State.objects.get(name='Active')
    ).order_by('-time')

    #   Tag Filter
    for tag_id in tag_ids:
        ideas = ideas.filter(tags__pk=tag_id).distinct()

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
    tags = Tag.objects.filter(
        taggit_taggeditem_items__content_type__name='idea',
        taggit_taggeditem_items__object_id__in=ideas
    ).annotate(count=Count('taggit_taggeditem_items')
               ).order_by('-count', 'name')[:25]

    for tag in tags:
        if tag.slug in tag_strs:
            tag_slugs = ",".join([s for s in tag_strs if s != tag.slug])
            tag.active = True
        else:
            tag_slugs = ",".join(tag_strs + [tag.slug])
            tag.active = False
        if tag_strs == [tag.slug]:
            tag.tag_url = "%s" % (reverse('idea:banner_detail',
                                          args=(banner_id,)))
        else:
            tag.tag_url = "%s?tags=%s" % (reverse('idea:banner_detail',
                                                  args=(banner_id,)),
                                          tag_slugs)

    return _render(request, 'idea/banner_detail.html', {
        'ideas': page,
        'tags': tags,  # list of tags associated with banner ideas
        'banner': banner,
        'is_current_banner': is_current_banner,
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
