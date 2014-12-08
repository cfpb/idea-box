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
                                                       'private',
                                                       'slug',
                                                       'start_date',
                                                       'end_date']))
except ImportError:
    pass

class ConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    search_fields = ['key', 'value']

class IdeaAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'banner')
    search_fields = ['title', 'text']
    exclude = ('tags',)
    actions = idea_actions

class VoteAdmin(admin.ModelAdmin):
    list_display = ('creator', 'idea')
    search_fields = ['creator', 'idea']
    actions = vote_actions

class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'private', 'start_date', 'end_date')
    fields = ('title', ('private', 'slug'), 'text', 'start_date', 'end_date')
    readonly_fields = ('slug',)
    search_fields = ['title', 'text']
    actions = banner_actions

admin.site.register(State)
admin.site.register(Config, ConfigAdmin)
admin.site.register(Idea, IdeaAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Banner, BannerAdmin)
