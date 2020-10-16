from django.urls import path, include
from .views import StravaTokenRedirectView

urlpatterns = [
    path('', StravaTokenRedirectView.as_view(), name='check_mtpu_strava_oauth'),
]
