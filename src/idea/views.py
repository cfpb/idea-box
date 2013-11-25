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
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST


from idea.forms import IdeaForm, IdeaTagForm, UpVoteForm
from idea.models import Idea, State, Vote, Banner
from idea.utility import state_helper
from idea.models import UP_VOTE
from core.taggit.models import Tag

def _render(req, template_name, context={}):
    context['active_app'] = 'Idea'
    context['app_link'] = reverse('idea:idea_list')
    return render(req, template_name, context)

def get_banner():
    today = date.today()
    timed_banners = Banner.objects.filter(start_date__lte=today, 
           end_date__isnull=False, end_date__gt=today)

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
    tag_strs= request.GET.get('tags', '').split(',')
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
        if sort_or_state == 'comment':
            ideas = ideas.order_by('-comment_count')
        elif sort_or_state == 'recent':
            ideas = ideas.order_by('-time')
        else:
            sort_or_state = 'vote'
            ideas = ideas.order_by('-vote_count')

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
            tag.tag_url = "%s"  %  (reverse('idea:idea_list',
                args=(sort_or_state,)))
            tag.active = True
        else:
            tag.tag_url = "%s?tags=%s"  %  (reverse('idea:idea_list',
                args=(sort_or_state,)), tag.slug)
            tag.active = False

    total_num_ideas = Idea.objects.all().count()

    banner = get_banner()

    return _render(request, 'idea/list.html', {
        'sort_or_state': sort_or_state,
        'ideas':    page,   
        'total_num_ideas': total_num_ideas,  
        'tags':     tags,   #   list of popular tags
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

        #Up voting is idempotent
        existing_votes = Vote.objects.filter(idea=idea, creator=request.user, vote=UP_VOTE)

        if not existing_votes.exists():
            vote_up(idea, request.user)

        return HttpResponseRedirect(next_url)

def more_like_text(text, klass):
    """
    Return more entries like the provided chunk of text. We have to jump
    through some hoops to get this working as the haystack API does not
    account for this case. In particular, this is a solr-specific hack.
    """
    back = backend.SearchBackend()
    if hasattr(back, 'conn'):
        params = {'fl': '*,score', 'stream.body': text}
        solr_results = back.conn.more_like_this('',
                back.site.get_index(klass).get_content_field(), **params)
        return back._process_results(solr_results)['results']
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
            idea.tags.add(*tags)
            #   Make sure the search index included the tags
            site.get_index(Idea).update_object(idea)
            return HttpResponseRedirect(
                    reverse('idea:idea_detail', args=(idea.id,)))
    else:
        tag_form = IdeaTagForm()

    voters = User.objects.filter(vote__idea=idea, vote__vote=UP_VOTE)

    for v in voters:
        try:
            v.profile =  v.get_profile()
        except (ObjectDoesNotExist, SiteProfileNotAvailable):
            v.profile = None

            
    idea_type = ContentType.objects.get(app_label="idea", model="idea")

    tags = idea.tags.extra(select={
        'tag_count': """
            SELECT COUNT(*) from taggit_taggeditem tt WHERE tt.tag_id = taggit_tag.id 
            AND content_type_id = %s 
        """
    }, select_params=[idea_type.id]).order_by('name')

    for tag in tags:
        tag.tag_url = "%s?tags=%s"  %  (reverse('idea:idea_list'), tag.slug)

    return _render(request, 'idea/detail.html', {
        'idea': idea,   #   title, body, user name, user photo, time
        'support': request.user in voters,
        'tags': tags, 
        'voters': voters,
        'tag_form': tag_form
        })

@login_required
def add_idea(request):
    banner = get_banner()
    if request.method == 'POST':
        idea = Idea(creator=request.user, state=state_helper.get_first_state())
        if idea.state.name == 'Active':
            form = IdeaForm(request.POST, instance=idea)
            if form.is_valid():
                new_idea = form.save()
                vote_up(new_idea, request.user)
                #   Make sure the search index included the tags
                site.get_index(Idea).update_object(new_idea)
                return HttpResponseRedirect(reverse('idea:idea_detail', args=(idea.id,)))
        else:
            return HttpResponse('Idea is archived', status=403)
    else:
        idea_title = request.GET.get('idea_title', '')
        form = IdeaForm(initial={'title':idea_title})
        return _render(request, 'idea/add.html', {
            'form':form,
            'banner':banner,
            'similar': [r.object for r in more_like_text(idea_title,
                Idea)]
            })
