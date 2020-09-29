from django import forms
from .models import *
from django.conf import settings
from bootstrap_datepicker_plus import DatePickerInput, TimePickerInput, DateTimePickerInput, MonthPickerInput, YearPickerInput
from sequence.models import Sequence, TransType, CameraMake
from django.db.models.expressions import F, Window
from django.db.models.functions.window import RowNumber
from django.db.models import Avg, Count, Min, Sum

def getAllCameraMake():
    camera_makes = CameraMake.objects.all()
    cm_choice = []
    if camera_makes.count() > 0:
        for camera_make in camera_makes:
            cm_choice.append((camera_make.pk, camera_make.name))
    cm_choice.append((-1, 'Others'))
    cm_choice = tuple(cm_choice)
    print(cm_choice)
    return cm_choice


class ChallengeForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}),
                           required=False)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}),
        required=False)

    transport_type = forms.ModelMultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'form-control'}),
        queryset=TransType.objects.filter(parent__isnull=False),
    )

    camera_make = forms.ModelMultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'form-control'}
        ),
        # choices=getAllCameraMake()
        queryset=CameraMake.objects.all()
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
    transport_type = forms.ModelChoiceField(
        required=False,
        widget=forms.Select(
            attrs={'class': 'form-control'}),
        queryset=TransType.objects.filter(parent__isnull=False),
        empty_label='All Types'
    )
    camera_make = forms.ModelMultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'form-control'}
        ),
        # choices=getAllCameraMake()
        queryset=CameraMake.objects.all()
    )

    # challenge_type = forms.ChoiceField(
    #     widget=forms.RadioSelect(attrs={'class': '', 'data-validation': 'required', 'value': '0'}),
    #     choices=(('0', 'All'), ('1', 'Active'), ('2', 'Completed')),
    #     required=False,
    # )

    start_time = forms.DateField(
        widget=DatePickerInput(
            format='YYYY-MM-DD',
            options={
                "format": 'YYYY-MM-DD',
                "showClose": False,
                "showClear": False,
                "showTodayButton": False,
            },
            attrs={'class': 'd-none'}
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
        ),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

