import math

import requests
from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.shortcuts import redirect
from django.urls import reverse
from datetime import datetime


def get_current_timestamp():
    current_time = str(int(datetime.now().timestamp()))
    return current_time


def send_mail_with_html(subject, html_message, to_email, reply_to, from_email=None):
    if isinstance(to_email, str):
        to = [to_email]
    else:
        to = to_email
    if isinstance(reply_to, str):
        reply_to = [reply_to]

    msg = EmailMultiAlternatives(
        subject=subject,
        from_email=from_email,
        to=to, 
        reply_to=reply_to
    )
    msg.attach_alternative(html_message, 'text/html')
    print(msg.send())


def my_login_required(function):
    def wrapper(request, *args, **kw):
        if not request.user.is_authenticated:
            return redirect('{}?next={}'.format(reverse('login'), request.path))
        else:
            return function(request, *args, **kw)
    return wrapper


def get_mapillary_user(token):
    # omit the bbox if you want to retrieve all data your account can access, it will automatically limit to your subscription area
    url = 'https://a.mapillary.com/v3/me?client_id=' + settings.MAPILLARY_CLIENT_ID
    headers = {"Authorization": "Bearer {}".format(token)}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data


def get_sequence_by_key(token, seq_key):
    if seq_key is None:
        return False
    url = 'https://a.mapillary.com/v3/sequences/{}?client_id={}'.format(seq_key, settings.MAPILLARY_CLIENT_ID)
    headers = {"Authorization": "Bearer {}".format(token)}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data


def distance(origin, destination):
    lon1, lat1 = origin
    lon2, lat2 = destination
    # km
    radius = 6371

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d


def check_mapillary_token(user, token=None):
    if token is None:
        if user.mapillary_access_token == '' or user.mapillary_access_token is None:
            return False
        map_user_data = get_mapillary_user(user.mapillary_access_token)
    else:
        map_user_data = get_mapillary_user(token)

    if map_user_data is None or 'message' in map_user_data.keys():
        return False
    else:
        return map_user_data


def get_url_with_params(url, params=None):
    if url is None or url == '':
        return ''
    import urllib.parse as urlparse
    from urllib.parse import parse_qs
    parsed = urlparse.urlparse(url)

    # url doesn't have params.
    main_url = url.split('?')[0]

    # target url
    url = ''

    basic_params = parse_qs(parsed.query)
    print(basic_params)

    if params is not None and isinstance(params, list):
        first = True
        for param in params:
            if param not in basic_params.keys():
                print(param)
                continue
            if first:
                url = '{}?{}={}'.format(main_url, param, parse_qs(parsed.query)[param][0])
                first = False
            else:
                url = '{}&{}={}'.format(url, param, parse_qs(parsed.query)[param][0])

    elif params is not None and isinstance(params, str) and params != '' and params in basic_params.keys():
        url = '{}?{}={}'.format(main_url, params, parse_qs(parsed.query)[params][0])
    return url


def get_youtube_embed_url(url):
    url = get_url_with_params(url, 'v')
    return url.replace('watch?v=', 'embed/')

