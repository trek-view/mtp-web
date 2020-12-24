import requests
from django.conf import settings
from mapbox import Geocoder
from django.conf import settings
from mapbox import Datasets
from mapbox import StaticStyle


def get_static_image(features, lon=None, lat=None):
    service = StaticStyle(access_token=settings.MAPBOX_ACCESS_TOKEN)
    response = service.image(
        username='mapbox',
        style_id='streets-v9',
        zoom=18,
        lon=lon,
        lat=lat,
        features=features,
    )
    return response