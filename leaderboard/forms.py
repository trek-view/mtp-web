## Django Packages
from django import forms
from django_select2 import forms as s2forms

## App packages
from .models import *
from datetime import datetime
from bootstrap_datepicker_plus import DatePickerInput, TimePickerInput, DateTimePickerInput, MonthPickerInput, YearPickerInput
from sequence.models import TransType
############################################################################
############################################################################

class LeaderboardSearchForm(forms.Form):

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
            required=True
        )

        self.fields['transport_type'] = forms.ModelChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'form-control'}),
            queryset=TransType.objects.all(),
            empty_label='All Types'
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

    def set_transport_type(self, transport_type):
        self.fields['transport_type'] = forms.ModelChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'form-control'}),
            queryset=TransType.objects.all(),
            empty_label='All Types',
            initial=transport_type
        )