## Django Packages
from django import forms
from django_select2 import forms as s2forms

## App packages
from .models import *
from datetime import datetime
from bootstrap_datepicker_plus import DatePickerInput, TimePickerInput, DateTimePickerInput, MonthPickerInput, YearPickerInput
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
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}),
        required=False)

        self.fields['transport_type'] = forms.ModelChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'form-control'}),
            queryset=TransportType.objects.filter(),
            empty_label=None
        )

        self.fields['tag'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.SelectMultiple(attrs={'class': 'form-control', 'data-validation': 'required'}),
            choices=getAllTags()
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

        self.fields['camera_make'] = forms.CharField(
            label='Camera Make/Model',
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        self.fields['transport_type'] = forms.ModelChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'form-control'}),
            queryset=TransportType.objects.filter(),
            empty_label='All Types'
        )
        self.fields['tag'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
            choices=getAllTags()
        )

class TourForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'] = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}),
                           required=False)

        self.fields['description'] = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}),
        required=False)

        self.fields['tag'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.SelectMultiple(attrs={'class': 'form-control', 'data-validation': 'required'}),
            choices=getAllTourTags()
        )

    class Meta:
        model = Tour
        fields = (
            'name',
            'description',
            'tag'
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

        self.fields['tag'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
            choices=getAllTourTags()
        )

