from django.contrib import admin
from idea.models import Idea, State, Vote, Banner, Config

idea_actions = []
vote_actions = []
banner_actions = []

try:
    from core.actions import export_as_csv_action

    idea_actions.append(export_as_csv_action("CSV Export",
                                             fields=['title',
                                                     'creator',
                                                     'is_anonymous',
                                                     'banner',
                                                     'summary',
                                                     'text',
                                                     'state']))
    vote_actions.append(export_as_csv_action("CSV Export",
                                             fields=['creator',
                                                     'idea']))
    banner_actions.append(export_as_csv_action("CSV Export",
                                               fields=['title',
                                                       'text',
                                                       'slug',
                                                       'is_private',
                                                       'is_votes',
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
    fields = ('creator', ('banner', 'is_anonymous'), 'title', 'summary', 'text', 'state')
    actions = idea_actions

class VoteAdmin(admin.ModelAdmin):
    list_display = ('creator', 'idea')
    search_fields = ['creator', 'idea']
    actions = vote_actions

class BannerAdmin(admin.ModelAdmin):
    def room_link_clickable(self, obj):
        return obj.room_link()
    room_link_clickable.allow_tags = True
    room_link_clickable.short_description = "room link"
    readonly_fields = ('room_link_clickable',)

    list_display = ('title', 'is_private', 'is_votes', 'start_date', 'end_date')
    fields = ('title', ('is_private', 'room_link_clickable', 'is_votes'), 'text', 'start_date', 'end_date')
    
    search_fields = ['title', 'summary']
    actions = banner_actions

    class Media:
        js = ("idea/js/admin.js",)

admin.site.register(State)
admin.site.register(Config, ConfigAdmin)
admin.site.register(Idea, IdeaAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Banner, BannerAdmin)
