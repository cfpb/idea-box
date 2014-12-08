from django.conf.urls import patterns, url


urlpatterns = patterns(
    'idea.views',
    url(r'^$', 'list'),
    url(r'^add/$', 'add_idea', name='add_idea'),
    url(r'^add/(?P<banner_id>\d+)/$', 'add_idea', name='add_idea'),
    url(r'^edit/(?P<idea_id>\d+)/$', 'edit_idea', name='edit_idea'),
    url(r'^list/$', 'list', name='idea_list'),
    url(r'^list/(?P<sort_or_state>\w+)/$', 'list', name='idea_list'),
    url(r'^detail/(?P<idea_id>\d+)/$', 'detail', name='idea_detail'),
    url(r'^detail/likes/(?P<idea_id>\d+)/$', 'show_likes', name='show_likes'),
    url(r'^detail/(?P<idea_id>\d+)/remove_tag/(?P<tag_slug>[a-zA-Z0-9/\-_]+)/$',
        'remove_tag', name='remove_tag'),
    url(r'^vote/up/$', 'up_vote', name='upvote_idea'),
    url(r'^challenge/(?P<banner_id>\d+)/$',
        'challenge_detail', name='challenge_detail'),
    url(r'^room/(?P<slug>.+)/$',
        'room_detail', name='room_detail'),
    url(r'challenge/list/$', 'banner_list', name='banner_list'),
)
