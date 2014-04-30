from django.contrib import admin
from idea.models import Idea, State, Vote, Banner, Config

idea_actions = []
vote_actions = []
banner_actions = []

try:
    from core.actions import export_as_csv_action

    idea_actions.append(export_as_csv_action("CSV Export",
                                             fields=['title',
                                                     'text',
                                                     'creator',
                                                     'banner']))
    vote_actions.append(export_as_csv_action("CSV Export",
                                             fields=['creator',
                                                     'idea']))
    banner_actions.append(export_as_csv_action("CSV Export",
                                               fields=['title',
                                                       'text',
                                                       'start_date',
                                                       'end_date']))
except ImportError:
    pass

class IdeaAdmin(admin.ModelAdmin):
    list_display = ('title', 'text', 'creator', 'banner')
    search_fields = ['title', 'text']
    exclude = ('tags',)
    actions = idea_actions

class VoteAdmin(admin.ModelAdmin):
    list_display = ('creator', 'idea')
    search_fields = ['creator', 'idea']
    actions = vote_actions

class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'text', 'start_date', 'end_date')
    search_fields = ['title', 'text']
    actions = banner_actions

admin.site.register(State)
admin.site.register(Config)
admin.site.register(Idea, IdeaAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Banner, BannerAdmin)
