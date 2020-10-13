## Django Packages
from django import forms
from django_select2 import forms as s2forms

## App packages
from .models import *
from tags_input import fields
from lib.classes import CustomTagsInputField
############################################################################
############################################################################

class GuidebookForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}),
        required=False
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}),
        required=False
    )
    category = forms.ModelChoiceField(
        required=False,
        widget=forms.Select(
            attrs={'class': 'form-control', 'data-validation': 'required'}),
        queryset=Category.objects.all(),
        to_field_name='pk',
        empty_label=None
    )

    tag = CustomTagsInputField(
        Tag.objects.filter(is_actived=True),
        create_missing=True,
        required=False,
        help_text='Add for a tag'
    )


    # cover_image = forms.FileField(
    #     widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'data-validation': 'required'}),
    #     required=False
    # )
    # is_published = forms.ChoiceField(
    #     widget=forms.RadioSelect(attrs={'class': 'd-none', 'disabled': 'disabled'}),
    #     choices=(('True', 'Published'), ('False', 'Unpublished')),
    #     required=False,
    #     label=''
    # )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['tag'] = CustomTagsInputField(
            Tag.objects.filter(is_actived=True),
            create_missing=True,
            required=False,
            help_text='Add for a tag'
        )

    class Meta:
        model = Guidebook
        fields = (
            'name',
            'description',
            # 'cover_image',
            'category',
            'tag',
            # 'is_published',
        )

class GuidebookImageForm(forms.ModelForm):
    cover_image = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Guidebook
        fields = (
            'cover_image',
        )

class SceneForm(forms.Form):
    image_key = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control d-none'}),
    )
    title = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scene Title'}),
    )
    description = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Scene Description', 'rows': 2, 'style': 'resize: none;'}),
        required=False
    )

    lat = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control d-none'}),
    )
    lng = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control d-none'}),
    )

    username = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control d-none'}),
    )

    start_x = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control d-none'}),
        required=False
    )

    start_y = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control d-none'}),
        required=False
    )

    class Meta:
        fields = (
            'image_key',
            'title',
            'description',
            'lat',
            'lng',
            'start_x',
            'start_y',
            'username'
        )

class PointOfInterestForm(forms.ModelForm):
    title = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Point of Interest Title'}),
    )
    description = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Point of Interest Description', 'rows': 3}),
        required=False
    )
    category = forms.ModelChoiceField(
        required=False,
        label='',
        widget=forms.Select(
            attrs={'class': 'form-control'}),
        queryset=POICategory.objects.all(),
        to_field_name='pk',
        empty_label=None
    )

    class Meta:
        model = PointOfInterest
        fields = (
            'title',
            'description'
        )

class GuidebookSearchForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'] = forms.CharField(
            label='Guidebook Name',
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        self.fields['image_key'] = forms.CharField(
            label='Image Key',
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        self.fields['category'] = forms.ModelChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'form-control'}),
            queryset=Category.objects.all(),
            empty_label="All Categories"
        )
        self.fields['tag'] = CustomTagsInputField(
            Tag.objects.filter(is_actived=True),
            create_missing=False,
            required=False,
        )
        self.fields['tag'].help_text = 'Search for a tag'

        self.fields['username'] = forms.CharField(
            label='Username',
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        self.fields['like'] = forms.ChoiceField(
            label='Like',
            widget=forms.RadioSelect(),
            required=False,
            choices=(('all', 'All'), ('true', 'Liked'), ('false', 'Unliked')),
        )

    def _my(self, username):
        self.fields['username'] = forms.CharField(
            label='Username',
            widget=forms.TextInput(attrs={'class': 'form-control d-none', 'value': username}),
            required=False
        )

