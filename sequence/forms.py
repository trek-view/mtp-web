# Django Packages
from django import forms
from django_select2 import forms as s2forms

# App packages
from .models import *
from datetime import datetime
from bootstrap_datepicker_plus import DatePickerInput, TimePickerInput, DateTimePickerInput, MonthPickerInput, YearPickerInput
from lib.classes import CustomTagsInputField
from django.db.models import Count
from django.db.models.expressions import Window
from django.db.models.functions.window import RowNumber
############################################################################
############################################################################


class TransportSearchForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        now = datetime.now()
        year = now.year
        month = now.month

        self.fields['month'] = forms.DateField(
            widget=MonthPickerInput(
                format="YYYY-MM",
                options={
                    "format": "YYYY-MM",
                    "showClose": False,
                    "showClear": False,
                    "showTodayButton": False,
                },
                attrs={
                    'value': str(year) + '-' + str(month)
                },
            ),
            required=False
        )

    def set_month(self, month):
        self.fields['month'] = forms.DateField(
            widget=MonthPickerInput(
                format="YYYY-MM",
                options={
                    "format": "YYYY-MM",
                    "showClose": False,
                    "showClear": False,
                    "showTodayButton": False,
                },
                attrs={
                    'value': month
                },
            ),
            required=False
        )


class AddSequeceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'] = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}),
                           required=False)

        self.fields['description'] = forms.CharField(
            widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation-optional': 'true'}),
            required=False
        )

        self.fields['transport_type'] = forms.ModelChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'form-control', 'data-validation': 'required'}),
            queryset=TransType.objects.filter(parent__isnull=False),
            empty_label=None
        )

        self.fields['tag'] = CustomTagsInputField(
            Tag.objects.filter(is_actived=True),
            create_missing=True,
            required=False,
            help_text='Add a tag'
        )

    class Meta:
        model = Sequence
        fields = (
            'name',
            'description',
            'transport_type',
            'tag'
        )


class SequenceSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'] = forms.CharField(
            label='Username',
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        self.fields['name'] = forms.CharField(
            label='Sequence Name',
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        self.fields['camera_make'] = forms.ModelMultipleChoiceField(
            required=False,
            widget=forms.SelectMultiple(
                attrs={'class': 'form-control'}
            ),
            queryset=CameraMake.objects.all(),
            label='Camera Make (leave blank for all)',
        )

        self.fields['transport_type'] = forms.ModelChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'form-control'}),
            queryset=TransType.objects.all(),
            empty_label='All Types'
        )
        self.fields['tag'] = CustomTagsInputField(
            Tag.objects.filter(is_actived=True),
            create_missing=False,
            required=False,
        )
        self.fields['tag'].help_text = 'Search for a tag'
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


def get_map_feature_values():
    map_feature_json = MapFeature.objects.all().values('value').annotate(
        image_count=Count('value')).order_by('-image_count').annotate(
        rank=Window(expression=RowNumber()))

    map_feature_values = [['all_values', 'All Values']]
    for map_feature in map_feature_json:
        map_feature_values.append([map_feature['value'], map_feature['value']])

    return tuple(map_feature_values)


class ImageSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['camera_make'] = forms.ModelMultipleChoiceField(
            required=False,
            widget=forms.SelectMultiple(
                attrs={'class': 'form-control'}
            ),
            queryset=CameraMake.objects.all(),
            label='Camera Make (leave blank for all)',
        )
        # self.fields['camera_model'] = forms.ModelMultipleChoiceField(
        #     required=False,
        #     widget=forms.SelectMultiple(
        #         attrs={'class': 'form-control'}
        #     ),
        #     queryset=CameraModel.objects.all()
        # )

        self.fields['username'] = forms.CharField(
            label='Username',
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        self.fields['transport_type'] = forms.ModelChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'form-control'}),
            queryset=TransType.objects.all(),
            empty_label='All Types'
        )

        self.fields['map_feature'] = forms.ChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'form-control'}),
            choices=get_map_feature_values(),
        )




class SequenceSearchForTourForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'] = forms.CharField(
            label='Sequence Name',
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        self.fields['camera_make'] = forms.CharField(
            label='Camera Make (leave blank for all)',
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        self.fields['transport_type'] = forms.ModelChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'form-control'}),
            queryset=TransType.objects.filter(),
            empty_label='All Types'
        )
        self.fields['tag'] = CustomTagsInputField(
            Tag.objects.filter(is_actived=True),
            create_missing=False,
            required=False,
        )
        self.fields['tag'].help_text = 'Search for a tag'
        self.fields['like'] = forms.ChoiceField(
            label='Like',
            widget=forms.RadioSelect(),
            required=False,
            choices=(('all', 'All'), ('true', 'Liked'), ('false', 'Unliked')),
        )
