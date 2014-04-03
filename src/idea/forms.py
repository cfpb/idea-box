from django import forms
from idea.models import Idea

class IdeaForm(forms.ModelForm):
    class Meta:
        model = Idea
        exclude = ('creator', 'time', 'state',)

    def __init__(self, *args, **kwargs):
        super(IdeaForm, self).__init__(*args, **kwargs)
        self.fields['banner'].empty_label = "No challenge"

    def clean_tags(self):
        """ Force tags to lowercase, since tags are case-sensitive otherwise. """

        if 'tags' in self.cleaned_data: 
            tags = self.cleaned_data['tags']
            #   Account for taggit's odd special case (when a tag with spaces
            #   but no commas is split)
            if 'tags' in self.data and u"," not in self.data['tags'] and len(tags) > 1:
                tags = [self.data['tags'].strip()]
            return [t.lower() for t in tags]
        

class UpVoteForm(forms.Form):
    idea_id = forms.IntegerField(widget=forms.HiddenInput())
    next = forms.CharField(max_length=512, widget=forms.HiddenInput())

class IdeaTagForm(forms.Form):
    tags = forms.CharField(max_length=512)

    def clean_tags(self):
        """ Force tags to lowercase, since tags are case-sensitive otherwise. """
        ts = self.cleaned_data['tags']
        return ts.lower()
