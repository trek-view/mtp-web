from django.http import HttpResponse, QueryDict
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import redirect
import re

from django.conf import settings

class AuthMd(MiddlewareMixin):
    """
        Middleware component that wraps the login_required decorator around
        matching URL patterns. To use, add the class to MIDDLEWARE_CLASSES and
        define LOGIN_REQUIRED_URLS and LOGIN_REQUIRED_URLS_EXCEPTIONS in your
        settings.py. For example:
        ------
        LOGIN_REQUIRED_URLS = (
            r'/topsecret/(.*)$',
        )
        LOGIN_REQUIRED_URLS_EXCEPTIONS = (
            r'/topsecret/login(.*)$',
            r'/topsecret/logout(.*)$',
        )
        ------
        LOGIN_REQUIRED_URLS is where you define URL patterns; each pattern must
        be a valid regex.

        LOGIN_REQUIRED_URLS_EXCEPTIONS is, conversely, where you explicitly
        define any exceptions (like login and logout URLs).
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        # No need to process URLs if user already logged in

        # get next url from request
        absolute_url = request.build_absolute_uri()
        path = request.path
        root_url = request.build_absolute_uri('/')[:-1].strip("/")
        sec_url = absolute_url.replace(root_url, '')
        q = QueryDict(mutable=True)
        q['next'] = sec_url
        next_url = q.urlencode(safe='/')


        if request.user.is_authenticated:
            if request.path == reverse('login') or request.path == reverse('signup'):
                return redirect('/')
            return None
        else:
            if path == reverse('oauth2_provider:authorize'):
                return redirect(reverse('login') + '?' + next_url)
        # Explicitly return None for all non-matching requests
        return None
