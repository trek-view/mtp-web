# Django Packages
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django import forms
from django.utils.text import capfirst
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)
from django.utils.translation import gettext, gettext_lazy as _

# App Packages
from .models import CustomUser, CustomBanner
from django.utils.html import mark_safe

UserModel = get_user_model()

############################################################################


class AuthenticationForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    email = forms.CharField(
        label=_("Email"),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '', 'autofocus': True})
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )

    error_messages = {
        'invalid_login': _(
            "Please enter a correct %(email)s and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }

    def __init__(self, request=None, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

        # Set the max length and label for the "username" field.
        self.email_field = UserModel._meta.get_field(UserModel.EMAIL_FIELD)
        if self.fields['email'].label is None:
            self.fields['email'].label = capfirst(self.email_field.verbose_name)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email is not None and password:
            email = email.lower()
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:

                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user(self):
        return self.user_cache

    def get_invalid_login_error(self):
        return forms.ValidationError(
            self.error_messages['invalid_login'],
            code='invalid_login',
            params={'email': self.email_field.verbose_name},
        )


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)


class UserSignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserSignUpForm, self).__init__(*args, **kwargs)

    email = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': ''}))

    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': ''}))

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': ''})
    )

    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': ''})
    )

    is_maillist = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'checked': 'checked'}),
        label='Email me about imagery capture competitions',
        required=False
    )

    is_term = forms.BooleanField(
        widget=forms.CheckboxInput(),
        label=mark_safe('<a href="https://www.trekview.org/terms" target="_blank">I agree to the Trek View terms of service</a>'),
        required=True
    )

    def clean_email(self):
        data = self.cleaned_data['email']
        return data.lower()

    class Meta:
        model = CustomUser
        fields = ("email", "username", "password1", "password2", "is_maillist")


class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': '', 'readonly': 'true'}))

    email = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'data-validation': 'required'}),
        required=False
    )

    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation-optional': 'true'}),
        required=False
    )

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-validation-optional': 'true'}),
        required=False
    )

    description = forms.CharField(
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'rows': 4, 'style': 'resize: none;', 'data-validation-optional': 'true'}),
        required=False
    )

    website_url = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'style': 'resize: none;', 'data-validation': 'url', 'data-validation-optional': 'true'}), required=False)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "description", "website_url")


class UserProfileForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control disabled', 'readonly': 'readonly'}), required=False)

    email = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': ''}))

    is_maillist = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'd-none', 'checked': 'checked'}),label='Email me about imagery capture competitions', required=False)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "is_maillist")


class UserPasswordChangeForm(PasswordChangeForm):

    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password', 'autofocus': True}),
    )

    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )


class UserAvatarForm(forms.ModelForm):
    avatar = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = CustomUser

        fields = (
            'avatar',
        )


class CustomBannerForm(forms.ModelForm):
    banner_text = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'form-control', 'data-validation': 'length', 'data-validation-length': 'max100', 'rows': 3}), required=False)

    linked_url = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'form-control', 'data-validation': 'url', 'data-validation-optional': 'true', 'rows': 3}),
        required=False)

    class Meta:
        model = CustomBanner
        fields = ("banner_text", 'linked_url')

