from django.contrib import admin
from idea.models import Idea,State,Vote, Banner

admin.site.register(State)
admin.site.register(Idea)
admin.site.register(Vote)
admin.site.register(Banner)
