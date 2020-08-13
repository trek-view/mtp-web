from django import forms
from .models import *
from django.conf import settings

class JobForm(forms.ModelForm):

    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}), required=False)
    organisation_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}), label='Organisation Name', required=False)
    organisation_website = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'data-validation': 'url'}), required=False, label='Organisation Website')
    organisation_category = None
    app_email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'data-validation': 'email'}), required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}), required=False)
    type = None
    capture_method = None
    iamge_quality = None
    geometry = forms.CharField(widget=forms.Textarea(attrs={'class': 'd-none'}), label='', required=False)
    zoom = forms.CharField(widget=forms.TextInput(attrs={'class': 'd-none'}), label='', required=False)

    is_published = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={'class': 'd-none', 'disabled': 'disabled'}),
        choices=(('True', 'Published'), ('False', 'Unpublished'))
    , required=False, label='')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['type'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple(attrs={'data-validation': 'checkbox_group', 'data-validation-qty': 'min1'}),
            choices=getAllCaptureType()
        )

        self.fields['capture_method'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple(attrs={'data-validation': 'checkbox_group', 'data-validation-qty': 'min1'}),
            choices=getAllCaptureMethod()
        )

        self.fields['organisation_category'] = forms.ChoiceField(
            widget=forms.Select(attrs={'class': 'form-control', 'data-validation': 'required'}),
            choices=getAllOrganisationCategory(), 
            label='Organisation Category', 
            required=False
        )

        self.fields['image_quality'] = forms.ChoiceField(
            widget=forms.RadioSelect(attrs={'class': '', 'data-validation': 'required'}),
            choices=getAllImageQuality(), 
            required=False
        )

    def set_is_approved(self, is_approved = None):
        if is_approved == 'approved':
            self.fields['is_published'] = forms.ChoiceField(
                widget=forms.RadioSelect(attrs={'class': '', 'data-validation': 'required'}),
                choices=(('True', 'Published'), ('False', 'Unpublished'))
            , required=False)
        elif is_approved == 'unapproved':
            self.fields['is_published'] = forms.ChoiceField(
                widget=forms.RadioSelect(attrs={'class': 'disabled', 'data-validation': 'required', 'disabled': 'disabled'}),
                choices=(('True', 'Published'), ('False', 'Unpublished'))
            , required=False)

    class Meta:
        model = Job
        fields = (
            # 'user_id',
            'name',
            'organisation_name',
            'organisation_website',
            'organisation_category',
            'app_email',
            'geometry',
            'description',
            'type',
            'capture_method',
            'image_quality',
            'zoom',
            'is_published'
        )

class JobSearchForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['type'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple(),
            choices=getAllCaptureType()
        )
        self.fields['capture_method'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple(),
            choices=getAllCaptureMethod()
        )
        self.fields['image_quality'] = forms.ChoiceField(
            widget=forms.RadioSelect(),
            choices=getAllImageQuality(), 
            required=False, 
        )


class JobApplicationForm(forms.ModelForm):

    subject = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}), required=False)
    # email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    # phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    # website = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}), required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}), required=False)

    class Meta:
        model = JobApplication
        fields = (
            # 'user_id',
            'subject',
            # 'email',
            # 'phone',
            # 'website',
            'description',
        )


class PhotographerForm(forms.ModelForm):

    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}), required=False)
    business_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}), required=False)
    business_website = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'data-validation': 'url'}), required=False)
    business_email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'data-validation': 'email'}), required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}), required=False)
    type = None
    capture_method = None
    image_quality = None
    geometry = forms.CharField(widget=forms.Textarea(attrs={'class': 'd-none'}), label='', required=False)
    zoom = forms.CharField(widget=forms.TextInput(attrs={'class': 'd-none'}), label='', required=False)

    is_published = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={'class': 'd-none', 'disabled': 'disabled'}),
        choices=(('True', 'Published'), ('False', 'Unpublished'))
    , required=False, label='')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['type'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple(attrs={'data-validation': 'checkbox_group', 'data-validation-qty': 'min1'}),
            choices=getAllCaptureType()
        )

        self.fields['capture_method'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple(attrs={'data-validation': 'checkbox_group', 'data-validation-qty': 'min1'}),
            choices=getAllCaptureMethod()
        )

        self.fields['image_quality'] = forms.ChoiceField(
            widget=forms.RadioSelect(attrs={'class': '', 'data-validation': 'required'}),
            choices=getAllImageQuality(), 
            required=False
        )

    def set_is_approved(self, is_approved = None):
        if is_approved == 'approved':
            self.fields['is_published'] = forms.ChoiceField(
                widget=forms.RadioSelect(attrs={'class': '', 'data-validation': 'required'}),
                choices=(('True', 'Published'), ('False', 'Unpublished'))
            , required=False)
        elif is_approved == 'unapproved':
            self.fields['is_published'] = forms.ChoiceField(
                widget=forms.RadioSelect(attrs={'class': 'disabled', 'data-validation': 'required', 'disabled': 'disabled'}),
                choices=(('True', 'Published'), ('False', 'Unpublished'))
            , required=False)

    class Meta:
        model = Photographer
        fields = (
            # 'user_id',
            'name',
            'business_name',
            'business_website',
            'business_email',
            'geometry',
            'description',
            'type',
            'capture_method',
            'image_quality',
            'zoom',
            'is_published'
        )

class PhotographerSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['type'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple(),
            choices=getAllCaptureType()
        )
        self.fields['capture_method'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple(),
            choices=getAllCaptureMethod()
        )
        self.fields['image_quality'] = forms.ChoiceField(
            widget=forms.RadioSelect(attrs={'class': '', 'data-validation': 'required'}),
            choices=getAllImageQuality(), 
            required=False
        )

class PhotographerEnquireForm(forms.ModelForm):

    subject = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation': 'required'}), required=False)
    # email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    # phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    # website = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}), required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'data-validation': 'required'}), required=False)

    class Meta:
        model = PhotographerEnquire
        fields = (
            # 'user_id',
            'subject',
            # 'email',
            # 'phone',
            # 'website',
            'description',
        )
