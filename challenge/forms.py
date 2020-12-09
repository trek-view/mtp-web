from bootstrap_datepicker_plus import DatePickerInput
from django import forms

from sequence.models import TransType, CameraMake, LabelType
from .models import *


def transport_types():
    types = TransType.objects.all()
    ts_types = [['all', 'All Types']]
    for t in types:
        ts_types.append([t.name, t.getFullName])
    ts_tuple = tuple(ts_types)
    return ts_tuple


def camera_makes():
    cms = CameraMake.objects.all()
    makes = []
    for cm in cms:
        makes.append([cm.name, cm.name])
    cm_tuple = tuple(makes)
    return cm_tuple


def label_types():
    label_type = [['all', 'All Types']]
    try:
        lts = LabelType.objects.filter(parent__isnull=False, source='mtpw')
        for lt in lts:
            label_type.append([lt.name, lt.getKey])
    except:
        pass
    return label_type


class ChallengeForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}),
                           required=False)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}),
        required=False)

    camera_make = forms.MultipleChoiceField(
        required=False,
        label='Camera Make (leave blank for all)',
        widget=forms.SelectMultiple(
            attrs={'class': 'selectpicker form-control border', 'multiple': 'multiple', 'data-live-search': 'true'}
        ),
        choices=camera_makes,
    )

    transport_type = forms.ChoiceField(
        required=False,
        widget=forms.Select(
            attrs={'class': 'selectpicker form-control border', 'data-live-search': 'true'}
        ),
        choices=transport_types,
    )

    geometry = forms.CharField(widget=forms.Textarea(attrs={'class': 'd-none'}), label='', required=False)

    zoom = forms.CharField(widget=forms.TextInput(attrs={'class': 'd-none'}), label='', required=False)

    start_time = forms.DateField(
        widget=DatePickerInput(
            format='YYYY-MM-DD',
            options={
                "format": 'YYYY-MM-DD',
                "showClose": False,
                "showClear": False,
                "showTodayButton": False,
            },
        ),
        required=False
    )

    end_time = forms.DateField(
        widget=DatePickerInput(
            format='YYYY-MM-DD',
            options={
                "format": 'YYYY-MM-DD',
                "showClose": False,
                "showClear": False,
                "showTodayButton": False,
            },
            attrs={
                'data-validation': 'end_time'
            }
        ),
        required=False
    )

    is_published = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={'class': 'd-none', 'disabled': 'disabled'}),
        choices=(('True', 'Published'), ('False', 'Unpublished'))
        , required=False, label='')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Challenge
        fields = (
            # 'user_id',
            'name',
            'geometry',
            'camera_make',
            'description',
            'start_time',
            'end_time',
            'transport_type',
            'zoom',
            'is_published'
        )


class ChallengeSearchForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}),
                           required=False)

    camera_make = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'selectpicker form-control border', 'multiple': 'multiple', 'data-live-search': 'true'}
        ),
        choices=camera_makes,
        label='Camera Make (leave blank for all)',
    )

    transport_type = forms.ChoiceField(
        required=False,
        widget=forms.Select(
            attrs={'class': 'selectpicker form-control border', 'data-live-search': 'true'}
        ),
        choices=transport_types,
    )

    challenge_type = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={'class': '', 'value': 'all'}),
        choices=(('all', 'All'), ('active', 'Active'), ('completed', 'Completed')),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LabelChallengeForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}),
                           required=False)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}),
        required=False)

    label_type = forms.ModelMultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'selectpicker form-control border', 'multiple': 'multiple', 'data-live-search': 'true'}
        ),
        queryset=LabelType.objects.filter(source='mtpw')
    )

    geometry = forms.CharField(widget=forms.Textarea(attrs={'class': 'd-none'}), label='', required=False)

    zoom = forms.CharField(widget=forms.TextInput(attrs={'class': 'd-none'}), label='', required=False)

    start_time = forms.DateField(
        widget=DatePickerInput(
            format='YYYY-MM-DD',
            options={
                "format": 'YYYY-MM-DD',
                "showClose": False,
                "showClear": False,
                "showTodayButton": False,
            },
        ),
        required=False
    )

    end_time = forms.DateField(
        widget=DatePickerInput(
            format='YYYY-MM-DD',
            options={
                "format": 'YYYY-MM-DD',
                "showClose": False,
                "showClear": False,
                "showTodayButton": False,
            },
            attrs={
                'data-validation': 'end_time'
            }
        ),
        required=False
    )

    is_published = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={'class': 'd-none', 'disabled': 'disabled'}),
        choices=(('True', 'Published'), ('False', 'Unpublished'))
        , required=False, label='')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = LabelChallenge
        fields = (
            'name',
            'geometry',
            'description',
            'start_time',
            'end_time',
            'zoom',
            'is_published',
            'label_type',
        )


class LabelChallengeSearchForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}),
                           required=False)
    label_type = forms.ChoiceField(
        required=False,
        widget=forms.Select(
            attrs={'class': 'selectpicker form-control border', 'data-live-search': 'true'}
        ),
        choices=label_types(),
    )

    challenge_type = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={'class': '', 'value': 'all'}),
        choices=(('all', 'All'), ('active', 'Active'), ('completed', 'Completed')),
        required=False,
        initial='all'
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
