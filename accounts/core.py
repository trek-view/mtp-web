from django.views.generic.base import RedirectView
from django.http.response import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.conf import settings


class MTPUResponseRedirect(HttpResponseRedirect):
    allowed_schemes = [settings.MTPU_SCHEME]


class MTPUResponsePermanentRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = [settings.MTPU_SCHEME]


class CustomRedirectView(RedirectView):
    def get(self, request, *args, **kwargs):
        url = self.get_redirect_url(*args, **kwargs)
        if url and not self.permanent:
            if self.permanent:
                return MTPUResponsePermanentRedirect(url)
            return MTPUResponseRedirect(url)
        else:
            super(CustomRedirectView, self).get(request, *args, **kwargs)
