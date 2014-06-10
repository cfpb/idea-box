from django import forms
from idea.models import Idea

try:
    from core.taggit.utils import add_tags
except ImportError:
    pass


class IdeaForm(forms.ModelForm):

    class Meta:
        model = Idea
        exclude = ('creator', 'time', 'state', 'voters')

    def __init__(self, *args, **kwargs):
        super(IdeaForm, self).__init__(*args, **kwargs)
        self.fields['banner'].empty_label = "Select"

        self.fields['title'].label = "What is your idea?"
        self.fields['banner'].label = None
        self.fields['summary'].label = "Pitch your idea"
        self.fields['tags'].label = "Tag it with keywords"
        self.fields['text'].label = "Give us the details"

        self.fields['challenge-checkbox'] = forms.BooleanField(
            required=False,
            label="My idea is part of a Challenge")

        for field in self.fields:
            form_classes = "form-control"
            if field == "banner" and 'challenge-checkbox' in self.data.keys() \
                    and self.data['challenge-checkbox'] == 'on':
                form_classes += " active"
            if field in self.data.keys() and self.data[field]:
                form_classes += " populated"
            self.fields[field].widget.attrs["class"] = form_classes

        self.fields.keyOrder = [
            'title',
            'challenge-checkbox',
            'banner',
            'summary',
            'tags',
            'text']

    def save(self, commit=True):
        instance = super(IdeaForm, self).save(commit=False)
        # add tags separately
        tags = self.cleaned_data.get('tags', [])
        self.cleaned_data['tags'] = []
        instance.save()
        try:
            for t in tags:
                add_tags(instance, t, None, instance.creator, 'idea')
        except NameError:  # catch if add_tags doesn't exist
            instance.tags.add(*tags)
        return instance

    def set_error_css(self):
        for field in self.fields:
            classes_set = set(self.fields[field].widget.attrs["class"].split())
            if field in self.errors.keys():
                classes_set.add("input-error")
            else:
                classes_set.discard("input-error")
            self.fields[field].widget.attrs["class"] = " ".join(classes_set)

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
    tags = forms.CharField(max_length=512,
                           widget=forms.TextInput(attrs={'class': 'tags_autocomplete'}))

    def clean_tags(self):
        """ Force tags to lowercase, since tags are case-sensitive otherwise. """
        ts = self.cleaned_data['tags']
        return ts.lower()
