from django.conf.urls import patterns, url
from django.views.generic.simple import redirect_to

urlpatterns = patterns('idea.views',
    url(r'^$', redirect_to, {'url': '/idea/list/'}),
    url(r'^add/$', 'add_idea', name='add_idea'),
    url(r'^list/$', 'list', name='idea_list'),
    url(r'^list/(?P<sort_or_state>\w+)/$', 'list', name='idea_list'),
    url(r'^detail/(?P<idea_id>\d+)/$', 'detail', name='idea_detail'),
    url(r'^vote/up/$', 'up_vote', name='upvote_idea')
)
