from django.conf import settings # import the settings file

def get_settings(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {
        'MAPBOX_PUBLISH_TOKEN': settings.MAPBOX_PUBLISH_TOKEN, 
        'GOOGLE_ANALYTICS': settings.GOOGLE_ANALYTICS, 
        'STATIC_URL': settings.STATIC_URL,
        'MAPILLARY_AUTHENTICATION_URL': settings.MAPILLARY_AUTHENTICATION_URL,
        'MAPILLARY_CLIENT_ID': settings.MAPILLARY_CLIENT_ID,
        'MAPILLARY_CLIENT_SECRET': settings.MAPILLARY_CLIENT_SECRET,
        'MEDIA_URL': settings.MEDIA_URL,
        'FONT_AWESOME_KIT': settings.FONT_AWESOME_KIT,
        'BASE_URL': settings.BASE_URL
    }

def baseurl(request):
    """
    Return a BASE_URL template context for the current request.
    """
    if request.is_secure():
        scheme = 'https://'
    else:
        scheme = 'http://'
        
    return {'BASE_URL': scheme + request.get_host(),}
