from django import forms
from .models import *
from django.conf import settings
from bootstrap_datepicker_plus import DatePickerInput, TimePickerInput, DateTimePickerInput, MonthPickerInput, YearPickerInput

class ChallengeForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}),
                           required=False)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}),
        required=False)
    transport_type = forms.ModelChoiceField(
        required=False,
        widget=forms.Select(
            attrs={'class': 'form-control'}),
        queryset=TransType.objects.filter(parent__isnull=False),
        empty_label='All Types'
    )
    expected_count = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
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
            'description',
            'start_time',
            'end_time',
            'expected_count',
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
    expected_count_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
    )

    expected_count_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
    )

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


