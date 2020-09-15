from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django_email_verification import urls as mail_urls
from django.conf import settings
from django.conf.urls.static import static
from two_factor.urls import urlpatterns as tf_urls
from two_factor.admin import AdminSiteOTPRequired, AdminSiteOTPRequiredMixin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.http import is_safe_url
from django.contrib.auth.views import redirect_to_login
from config.sitemaps import StaticViewSitemap
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import GenericSitemap
from photographer.models import Photographer
from guidebook.models import Guidebook
from django.contrib import admin as admin_tmp
from accounts import views as account_views
from . import views

sitemaps = {
    'static': StaticViewSitemap,
    'photographer': GenericSitemap({
        'queryset': Photographer.objects.filter(is_published=True),
    }, priority=0.9),
    'guidebook': GenericSitemap({
        'queryset': Guidebook.objects.filter(is_published=True, is_approved=True),
    }, priority=0.9),
}

class AdminSiteOTPRequiredMixinRedirSetup(AdminSiteOTPRequired):
    def login(self, request, extra_context=None):
        redirect_to = request.POST.get(
            REDIRECT_FIELD_NAME, request.GET.get(REDIRECT_FIELD_NAME)
        )
        # For users not yet verified the AdminSiteOTPRequired.has_permission
        # will fail. So use the standard admin has_permission check:
        # (is_active and is_staff) and then check for verification.
        # Go to index if they pass, otherwise make them setup OTP device.
        if request.method == "GET" and super(
            AdminSiteOTPRequiredMixin, self
        ).has_permission(request):
            # Already logged-in and verified by OTP
            if request.user.is_verified():
                # User has permission
                index_path = reverse("admin:index", current_app=self.name)
            else:
                # User has permission but no OTP set:
                index_path = reverse("two_factor:setup", current_app=self.name)
            return HttpResponseRedirect(index_path)

        if not redirect_to or not is_safe_url(
            url=redirect_to, allowed_hosts=[request.get_host()]
        ):
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

        return redirect_to_login(redirect_to)


# handler404 = marketplaceViews.handler404
# handler500 = marketplaceViews.handler500

# admin.site.__class__ = AdminSiteOTPRequiredMixinRedirSetup

urlpatterns = [
    # path('', views.index, name='home'),
    path('', views.index, name='home'),
    # path('', RedirectView.as_view(url='marketplace', permanent=False), name='home'),

    path('accounts/', include('accounts.urls')),
    path('email/', include(mail_urls)),
    path('hire/', include('photographer.urls')),
    path('challenge/', include('challenge.urls')),
    path('guidebook/', include('guidebook.urls')),
    path('sequence/', include('sequence.urls')),
    path('tour/', include('tour.urls')),
    path('leaderboard/', include('leaderboard.urls')),
    path('user/<str:username>/profile/', account_views.profile, name="account.profile"),
    path('tags_input/', include('tags_input.urls', namespace='tags_input')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    re_path(r'', include(tf_urls)),
    path('mission-control/', admin.site.urls, name='admin'),
    path('api/', include('api.urls')),
]

# This part is for deploying this project as a production(DEBUG=True) on heroku.
if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ]