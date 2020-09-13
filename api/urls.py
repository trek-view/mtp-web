from django.urls import path, re_path
from . import views
from rest_framework_simplejwt import views as jwt_views
urlpatterns = [
    re_path(r'^(?P<version>(v1))/mapillary/token/verify', views.MapillaryTokenVerify.as_view(), name='api.mapillary.token_verify'),
    re_path(r'^(?P<version>(v1))/sequence/create', views.SequenceCreate.as_view(), name="api.sequence.create"),
    re_path(r'^(?P<version>(v1))/sequence/import/(?P<unique_id>[\w-]+)/$', views.SequenceImport.as_view(), name="api.sequence.import"),
    # re_path(r'^(?P<version>(v1|v2))/sequence/import', views.SequenceImport.as_view(), name="api.sequence.import"),
]