from django.urls import path, re_path
from . import views
from lib.rest_framework_mvt_views import mvt_view_factory
from sequence.models import Sequence, Image
from guidebook.models import Scene
from rest_framework_simplejwt import views as jwt_views
urlpatterns = [
    # re_path(r'^(?P<version>(v1))/mapillary/token/verify', views.MapillaryTokenVerify.as_view(), name='api.mapillary.token_verify'),
    re_path(r'^(?P<version>(v1))/sequence/create', views.SequenceCreate.as_view(), name="api.sequence.create"),
    re_path(r'^(?P<version>(v1))/sequence/import/(?P<unique_id>[\w-]+)/$', views.SequenceImport.as_view(), name="api.sequence.import"),
    # re_path(r'^(?P<version>(v1|v2))/sequence/import', views.SequenceImport.as_view(), name="api.sequence.import"),
    re_path(r'^(?P<version>(v1))/sequence.mvt', mvt_view_factory(model_class=Sequence, geom_col='geometry_coordinates'), name="api.sequence.mvt"),
    re_path(r'^(?P<version>(v1))/image.mvt', mvt_view_factory(model_class=Image, geom_col='point'), name="api.sequence.image_mvt"),
    re_path(r'^(?P<version>(v1))/scene.mvt', mvt_view_factory(model_class=Scene, geom_col='point'), name="api.guidebook.scene_mvt"),
    re_path(r'^(?P<version>(v1))/tour/(?P<tour_unique_id>[\w-]+)/sequence.mvt', mvt_view_factory(model_class=Sequence, geom_col='geometry_coordinates'), name="api.tour.sequence_mvt"),
    re_path(r'^(?P<version>(v1))/tour/(?P<tour_unique_id>[\w-]+)/image.mvt',
            mvt_view_factory(model_class=Image, geom_col='point'), name="api.tour.image_mvt"),
]
