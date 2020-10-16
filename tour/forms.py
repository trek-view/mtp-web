# Django Packages
from django import forms

from lib.classes import CustomTagsInputField
## App packages
from .models import *

############################################################################
############################################################################


class TourForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'] = forms.CharField(
            widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}),
            required=False
        )

        self.fields['description'] = forms.CharField(
            widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}),
            required=False
        )

        self.fields['tour_tag'] = CustomTagsInputField(
            TourTag.objects.filter(is_actived=True),
            create_missing=True,
            required=False,
        )

        self.fields['tour_tag'].help_text = 'Add a tag'

    class Meta:
        model = Tour
        fields = (
            'name',
            'description',
            'tour_tag'
        )


class TourSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'] = forms.CharField(
            label='Username',
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        self.fields['name'] = forms.CharField(
            label='Tour Name',
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        self.fields['tour_tag'] = CustomTagsInputField(
            TourTag.objects.filter(is_actived=True),
            create_missing=False,
            required=False,
        )
        self.fields['tour_tag'].help_text = 'Search for a tag'

        self.fields['like'] = forms.ChoiceField(
            label='Like',
            widget=forms.RadioSelect(),
            required=False,
            choices=(('all', 'All'), ('true', 'Liked'), ('false', 'Unliked')),
        )

    def _my(self, username):
        self.fields['username'] = forms.CharField(
            label='',
            widget=forms.TextInput(attrs={'class': 'form-control d-none', 'value': username}),
            required=False
        )
