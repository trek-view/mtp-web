# Django Packages
# App packages
from datetime import datetime

from bootstrap_datepicker_plus import MonthPickerInput
from django import forms

from sequence.models import TransType, CameraMake


############################################################################
############################################################################


def transport_types():
    types = TransType.objects.all()
    ts_types = [['all', 'All Types']]
    for t in types:
        ts_types.append([t.name, t.getFullName])
    ts_tuple = tuple(ts_types)
    return ts_tuple


def camera_make():
    cms = CameraMake.objects.all()
    makes = []
    for cm in cms:
        makes.append([cm.name, cm.name])
    cm_tuple = tuple(makes)
    return cm_tuple


class LeaderboardSearchForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        now = datetime.now()
        year = now.year
        month = now.month

        self.fields['transport_type'] = forms.ChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'selectpicker form-control border', 'data-live-search': 'true'}),
            choices=transport_types(),
        )

        self.fields['camera_make'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.SelectMultiple(
                attrs={'class': 'selectpicker form-control border', 'multiple': 'multiple', 'data-live-search': 'true'}
            ),
            choices=camera_make()
        )

        self.fields['time_type'] = forms.CharField(
            label='',
            widget=forms.TextInput(attrs={'class': 'form-control d-none'}),
            required=False
        )

        self.fields['filter_type'] = forms.ChoiceField(
            widget=forms.RadioSelect,
            choices=((0, 'Uploads'), (1, 'Distance'), (2, 'Viewpoints')),
            initial=0,
            required=False
        )

    def set_timely(self, type, value):
        self.fields['time'] = forms.DateField(
            widget=MonthPickerInput(
                format=type,
                options={
                    "format": type,
                    "showClose": False,
                    "showClear": False,
                    "showTodayButton": False,
                },
                attrs={
                    'value': value
                },
            ),
            required=False
        )

    def set_transport_type(self, transport_type):
        self.fields['transport_type'] = forms.ChoiceField(
            required=False,
            widget=forms.Select(
                attrs={'class': 'selectpicker form-control border', 'data-live-search': 'true'}),
            choices=transport_types(),
            initial=transport_type
        )

    def set_filter_type(self, filter_type):
        self.fields['filter_type'] = forms.ChoiceField(widget=forms.RadioSelect, choices=((0, 'Uploads'), (1, 'Distance'), (2, 'Viewpoints')), initial=filter_type)

    def set_time_type(self, time_type):
        self.fields['time_type'] = forms.CharField(
            label='',
            widget=forms.TextInput(attrs={'class': 'form-control d-none', 'value': time_type}),
            required=False
        )

    def set_camera_makes(self, camera_makes):
        self.fields['camera_make'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.SelectMultiple(
                attrs={'class': 'selectpicker form-control border', 'multiple': 'multiple', 'data-live-search': 'true'}
            ),
            choices=camera_make(),
            initial=camera_makes
        )
