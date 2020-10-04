## Python packages
from datetime import datetime
import json
import re
from binascii import a2b_base64
import os

## Django Packages
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.http import (
    Http404, HttpResponse, JsonResponse, HttpResponsePermanentRedirect, HttpResponseRedirect,
)
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.db.models import Avg, Count, Min, Sum
from django.db.models.expressions import F, Window
from django.db.models.functions.window import RowNumber
from django.contrib.gis.geos import Point, Polygon, MultiPolygon, LinearRing, LineString
from django.db import transaction
from django.core import files
## Custom Libs ##
from lib.functions import *
from lib.mapillary import Mapillary
from lib.weatherstack import Weatherstack
import threading
from asgiref.sync import sync_to_async
## Project packages
from accounts.models import CustomUser, MapillaryUser
from tour.models import Tour, TourSequence
from guidebook.models import Guidebook, Scene

## App packages

# That includes from .models import *
from .forms import * 

############################################################################

MAIN_PAGE_DESCRIPTION = "Sequences are collections of images continuously captured by a user at a give time. Browse those created by others, or import your own from Mapillary."
IMPORT_PAGE_DESCRIPTION = "First start by choosing the month your sequences we're captured. If they were taken over multiple months, don't worry, once you've selected all the ones you want from the current month you can change this filter to add more."

############################################################################

def index(request):
    return redirect('sequence.sequence_list')

@my_login_required
def import_sequence(request):
    map_user_data = check_mapillary_token(request.user)
    if not map_user_data:
        return redirect(settings.MAPILLARY_AUTHENTICATION_URL)
    else:
        return redirect('sequence.import_sequence_list')

def sequence_list(request):
    sequences = None
    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        form = SequenceSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            camera_makes = form.cleaned_data['camera_make']
            tags = form.cleaned_data['tag']
            transport_type = form.cleaned_data['transport_type']
            username = form.cleaned_data['username']
            like = form.cleaned_data['like']


            sequences = Sequence.objects.all().filter(
                is_published=True
            ).exclude(image_count=0)
            if name and name != '':
                sequences = sequences.filter(name__contains=name)
            if not camera_makes is None and len(camera_makes) > 0:
                sequences = sequences.filter(camera_make__in=camera_makes)
            if transport_type and transport_type != 0 and transport_type != '':
                children_trans_type = TransType.objects.filter(parent_id=transport_type)
                if children_trans_type.count() > 0:
                    types = []
                    types.append(transport_type)
                    for t in children_trans_type:
                        types.append(t.pk)
                    sequences = sequences.filter(transport_type_id__in=types)
                else:
                    sequences = sequences.filter(transport_type_id=transport_type)
            if username and username != '':
                users = CustomUser.objects.filter(username__contains=username)
                sequences = sequences.filter(user__in=users)
            if len(tags) > 0:
                for tag in tags:
                    sequences = sequences.filter(tag=tag)
            if like and like != 'all':
                sequence_likes = SequenceLike.objects.all().values('sequence').annotate()
                print(sequence_likes)
                sequence_ary = []
                if sequence_likes.count() > 0:
                    for sequence_like in sequence_likes:
                        sequence_ary.append(sequence_like['sequence'])
                if like == 'true':
                    sequences = sequences.filter(pk__in=sequence_ary)
                elif like == 'false':
                    sequences = sequences.exclude(pk__in=sequence_ary)

            filter_time = request.GET.get('time')
            time_type = request.GET.get('time_type')

            print('count: ', sequences.count())
            if time_type is None or not time_type or time_type == 'all_time':
                sequences = sequences
            else:
                if time_type == 'monthly':
                    if filter_time is None or filter_time == '':
                        now = datetime.now()
                        y = now.year
                        m = now.month
                    else:
                        y = filter_time.split('-')[0]
                        m = filter_time.split('-')[1]
                    print(m)
                    print(y)
                    sequences = sequences.filter(
                        captured_at__month=m,
                        captured_at__year=y
                    )

                elif time_type == 'yearly':
                    print(filter_time)
                    if filter_time is None or filter_time == '':
                        now = datetime.now()
                        y = now.year
                    else:
                        y = filter_time
                    sequences = sequences.filter(
                        captured_at__year=y
                    )

            print('count: ', sequences.count())

    if sequences == None:
        sequences = Sequence.objects.all().filter(is_published=True).exclude(image_count=0)
        form = SequenceSearchForm()

    paginator = Paginator(sequences.order_by('-created_at'), 5)

    try:
        pSequences = paginator.page(page)
    except PageNotAnInteger:
        pSequences = paginator.page(1)
    except EmptyPage:
        pSequences = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pSequences.number < 4:
            first_num = 1
            last_num = 7
        elif pSequences.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pSequences.number - 3
            last_num = pSequences.number + 3
    pSequences.paginator.pages = range(first_num, last_num + 1)
    pSequences.count = len(pSequences)

    for i in range(len(pSequences)):
        tour_sequences = TourSequence.objects.filter(sequence_id=pSequences[i].pk)
        if tour_sequences is None or not tour_sequences:
            pSequences[i].tour_count = 0
        else:
            pSequences[i].tour_count = tour_sequences.count()


    content = {
        'sequences': pSequences,
        'form': form,
        'pageName': 'Sequences',
        'pageTitle': 'Sequences',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page
    }
    return render(request, 'sequence/list.html', content)

@my_login_required
def my_sequence_list(request):
    sequences = None
    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        form = SequenceSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            camera_makes = form.cleaned_data['camera_make']
            tags = form.cleaned_data['tag']
            transport_type = form.cleaned_data['transport_type']
            like = form.cleaned_data['like']

            sequences = Sequence.objects.all().filter(
                user=request.user
            ).exclude(image_count=0)
            if name and name != '':
                sequences = sequences.filter(name__contains=name)
            if not camera_makes is None and len(camera_makes) > 0:
                sequences = sequences.filter(camera_make__in=camera_makes)
            if transport_type and transport_type != 0 and transport_type != '':
                children_trans_type = TransType.objects.filter(parent_id=transport_type)
                if children_trans_type.count() > 0:
                    types = []
                    types.append(transport_type)
                    for t in children_trans_type:
                        types.append(t.pk)
                    sequences = sequences.filter(transport_type_id__in=types)
                else:
                    sequences = sequences.filter(transport_type_id=transport_type)
            if len(tags) > 0:
                for tag in tags:
                    sequences = sequences.filter(tag=tag)
            if like and like != 'all':
                sequence_likes = SequenceLike.objects.all().values('sequence').annotate()
                print(sequence_likes)
                sequence_ary = []
                if sequence_likes.count() > 0:
                    for sequence_like in sequence_likes:
                        sequence_ary.append(sequence_like['sequence'])
                if like == 'true':
                    sequences = sequences.filter(pk__in=sequence_ary)
                elif like == 'false':
                    sequences = sequences.exclude(pk__in=sequence_ary)

    if sequences == None:
        sequences = Sequence.objects.all().filter(is_published=True).exclude(image_count=0)
        form = SequenceSearchForm()

    paginator = Paginator(sequences.order_by('-created_at'), 5)

    try:
        pSequences = paginator.page(page)
    except PageNotAnInteger:
        pSequences = paginator.page(1)
    except EmptyPage:
        pSequences = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pSequences.number < 4:
            first_num = 1
            last_num = 7
        elif pSequences.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pSequences.number - 3
            last_num = pSequences.number + 3
    pSequences.paginator.pages = range(first_num, last_num + 1)
    pSequences.count = len(pSequences)

    for i in range(len(pSequences)):
        tour_sequences = TourSequence.objects.filter(sequence_id=pSequences[i].pk)
        if tour_sequences is None or not tour_sequences:
            pSequences[i].tour_count = 0
        else:
            pSequences[i].tour_count = tour_sequences.count()
    form._my(request.user.username)
    content = {
        'sequences': pSequences,
        'form': form,
        'pageName': 'My Sequences',
        'pageTitle': 'My Sequences',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page
    }
    return render(request, 'sequence/list.html', content)

def image_leaderboard(request):
    images = None
    page = 1
    m_type = None
    image_view_points = ImageViewPoint.objects.filter()
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        form = ImageSearchForm(request.GET)
        if form.is_valid():
            username = form.cleaned_data['username']
            camera_makes = form.cleaned_data['camera_make']
            # camera_models = form.cleaned_data['camera_model']
            transport_type = form.cleaned_data['transport_type']

            images = Image.objects.all()
            if not camera_makes is None and len(camera_makes) > 0:
                images = images.filter(camera_make__in=camera_makes)
            # if not camera_models is None and len(camera_models) > 0:
            #     images = images.filter(camera_model__in=camera_models)

            if transport_type and transport_type != 0 and transport_type != '':
                children_trans_type = TransType.objects.filter(parent_id=transport_type)
                if children_trans_type.count() > 0:
                    types = []
                    types.append(transport_type)
                    for t in children_trans_type:
                        types.append(t.pk)
                    sequences = Sequence.objects.filter(transport_type_id__in=types)
                else:
                    sequences = Sequence.objects.filter(transport_type_id=transport_type)

                images = images.filter(sequence__in=sequences)

            m_type = request.GET.get('type')
            if username and username != '':
                if m_type is None or m_type == 'received':
                    users = CustomUser.objects.filter(username__contains=username)
                    images = images.filter(user__in=users)
                elif m_type == 'marked':
                    users = CustomUser.objects.filter(username__contains=username)
                    image_view_points = image_view_points.filter(user__in=users)

    if images == None:
        images = Image.objects.all()

    images = images.exclude(sequence=None)

    image_view_points_json = image_view_points.filter(image__in=images).values('image').annotate(image_count=Count('image')).order_by('-image_count').annotate(
        rank=Window(expression=RowNumber()))

    paginator = Paginator(image_view_points_json, 10)
    page = 1
    page = request.GET.get('page')
    if not page or page is None:
        page = 1
    try:
        pItems = paginator.page(page)
    except PageNotAnInteger:
        pItems = paginator.page(1)
    except EmptyPage:
        pItems = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pItems.number < 4:
            first_num = 1
            last_num = 7
        elif pItems.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pItems.number - 3
            last_num = pItems.number + 3
    pItems.paginator.pages = range(first_num, last_num + 1)
    pItems.count = len(pItems)
    form = ImageSearchForm(request.GET)


    for i in range(len(pItems)):
        image = images.get(pk=pItems[i]['image'])

        if image is None or not image:
            continue
        img = {}
        img['unique_id'] = image.unique_id
        img['image_key'] = image.image_key

        if image.camera_make is None:
            img['camera_make'] = ''
        else:
            img['camera_make'] = image.camera_make

        if image.camera_model is None:
            img['camera_model'] = ''
        else:
            img['camera_model'] = image.camera_model

        if image.captured_at is None:
            img['captured_at'] = ''
        else:
            img['captured_at'] = image.captured_at

        if image.user_key is None:
            img['user_key'] = ''
        else:
            img['user_key'] = image.user_key

        if image.username is None:
            img['username'] = ''
        else:
            img['username'] = image.username

        if image.user is None:
            img['user'] = ''
        else:
            img['user'] = image.user

        if image.organization_key is None:
            img['organization_key'] = ''
        else:
            img['organization_key'] = image.organization_key

        if image.point is None:
            img['point'] = [0, 0]
        else:
            img['point'] = [image.point.coords[0], image.point.coords[1]]

        try:
            img['transport_parent_icon'] = image.sequence.transport_type.parent.icon.font_awesome
        except:
            img['transport_parent_icon'] = ''

        try:
            img['transport_parent'] = image.sequence.transport_type.parent.name
        except:
            img['transport_parent'] = ''

        try:
            img['transport_icon'] = image.sequence.transport_type.icon.font_awesome
        except:
            img['transport_icon'] = ''

        try:
            img['transport'] = image.sequence.transport_type.name
        except:
            img['transport'] = ''

        try:
            img['sequence_unique_id'] = str(image.sequence.unique_id)
        except:
            img['sequence_unique_id'] = ''


        pItems[i]['image'] = img


    content = {
        'items': pItems,
        'form': form,
        'pageName': 'Images',
        'pageTitle': 'Images',
        'pageDescription': 'This is image learderboard.',
        'page': page
    }
    return render(request, 'sequence/image_leaderboard.html', content)

def save_weather(sequence):
    sequence_weathers = SequenceWeather.objects.filter(sequence=sequence)
    if sequence_weathers.count() == 0:
        weatherstack = Weatherstack()

        point = [sequence.getFirstPointLat(), sequence.getFirstPointLng()]
        if isinstance(sequence.captured_at, str):
            historical_date = sequence.captured_at[0:10]
        else:
            historical_date = sequence.captured_at.strftime('%Y-%m-%d')
        print(point)
        print('historical_date: ', historical_date)
        weather_json = weatherstack.get_historical_data(point=point, historical_date=historical_date)
        print(weather_json)

        if weather_json:
            sequence_weather = SequenceWeather()

            sequence_weather.sequence = sequence

            if 'location' in weather_json.keys():
                location = weather_json['location']
                if 'name' in location.keys():
                    sequence_weather.location_name = location['name']
                if 'country' in location.keys():
                    sequence_weather.location_country = location['country']
                if 'region' in location.keys():
                    sequence_weather.location_region = location['region']
                if 'lat' in location.keys():
                    sequence_weather.location_lat = float(location['lat'])
                if 'lon' in location.keys():
                    sequence_weather.location_lon = float(location['lon'])
                if 'timezone_id' in location.keys():
                    sequence_weather.location_timezone_id = location['timezone_id']
                if 'localtime' in location.keys():
                    sequence_weather.location_localtime = location['localtime']
                if 'localtime_epoch' in location.keys():
                    sequence_weather.location_localtime_epoch = location['localtime_epoch']
                if 'utc_offset' in location.keys():
                    sequence_weather.location_utc_offset = location['utc_offset']

            if 'current' in weather_json.keys():
                current = weather_json['current']
                if 'observation_time' in current.keys():
                    sequence_weather.current_observation_time = current['observation_time']
                if 'temperature' in current.keys():
                    sequence_weather.current_temperature = current['temperature']
                if 'weather_code' in current.keys():
                    sequence_weather.current_weather_code = current['weather_code']
                if 'weather_icons' in current.keys():
                    sequence_weather.current_weather_icons = current['weather_icons']
                if 'weather_descriptions' in current.keys():
                    sequence_weather.current_weather_descriptions = current['weather_descriptions']
                if 'wind_speed' in current.keys():
                    sequence_weather.current_wind_speed = current['wind_speed']
                if 'wind_degree' in current.keys():
                    sequence_weather.current_wind_degree = current['wind_degree']
                if 'wind_dir' in current.keys():
                    sequence_weather.current_wind_dir = current['wind_dir']
                if 'pressure' in current.keys():
                    sequence_weather.current_pressure = current['pressure']
                if 'precip' in current.keys():
                    sequence_weather.current_precip = current['precip']
                if 'humidity' in current.keys():
                    sequence_weather.current_humidity = current['humidity']
                if 'cloudcover' in current.keys():
                    sequence_weather.current_cloudcover = current['cloudcover']
                if 'feelslike' in current.keys():
                    sequence_weather.current_feelslike = current['feelslike']
                if 'uv_index' in current.keys():
                    sequence_weather.current_uv_index = current['uv_index']
                if 'is_day' in current.keys():
                    sequence_weather.current_is_day = current['is_day']

            if 'historical' in weather_json.keys():
                historical = weather_json['historical']
                if historical_date in historical.keys():
                    historical_data = historical[historical_date]
                    if 'date' in historical_data.keys():
                        sequence_weather.his_date = historical_data['date']
                    if 'date_epoch' in historical_data.keys():
                        sequence_weather.his_date_epoch = historical_data['date_epoch']
                    if 'astro' in historical_data.keys():
                        astro = historical_data['astro']
                        if 'sunrise' in astro.keys():
                            sequence_weather.his_astro_sunrise = astro['sunrise']
                        if 'sunset' in astro.keys():
                            sequence_weather.his_astro_sunset = astro['sunset']
                        if 'moonrise' in astro.keys():
                            sequence_weather.his_astro_moonrise = astro['moonrise']
                        if 'moonset' in astro.keys():
                            sequence_weather.his_astro_moonset = astro['moonset']
                        if 'moon_phase' in astro.keys():
                            sequence_weather.his_astro_moon_phase = astro['moon_phase']
                        if 'moon_illumination' in astro.keys():
                            sequence_weather.his_astro_moon_illumination = astro['moon_illumination']

                    if 'mintemp' in historical_data.keys():
                        sequence_weather.his_mintemp = historical_data['mintemp']
                    if 'maxtemp' in historical_data.keys():
                        sequence_weather.his_maxtemp = historical_data['maxtemp']
                    if 'avgtemp' in historical_data.keys():
                        sequence_weather.his_avgtemp = historical_data['avgtemp']
                    if 'totalsnow' in historical_data.keys():
                        sequence_weather.his_totalsnow = historical_data['totalsnow']
                    if 'sunhour' in historical_data.keys():
                        sequence_weather.his_sunhour = historical_data['sunhour']
                    if 'uv_index' in historical_data.keys():
                        sequence_weather.his_uv_index = historical_data['uv_index']
                    if 'hourly' in historical_data.keys():
                        hourly_data = historical_data['hourly']
                        if len(hourly_data) > 0:
                            different_time = 24
                            d_index = 0
                            for h_index in range(len(hourly_data)):
                                if 'time' in hourly_data[h_index].keys():
                                    time_str = hourly_data[h_index]['time']
                                    time_float = float(time_str) / 100
                                    capture_h = float(sequence.captured_at.strftime('%H'))
                                    capture_m = float(sequence.captured_at.strftime('%M'))
                                    d_time = abs(capture_h + capture_m / 60 - time_float)
                                    if d_time < different_time:
                                        d_index = h_index
                                        different_time = d_time

                            h_data = hourly_data[d_index]
                            if 'time' in h_data.keys():
                                sequence_weather.his_hourly_time = h_data['time']
                            if 'temperature' in h_data.keys():
                                sequence_weather.his_hourly_temperature = h_data['temperature']
                            if 'wind_speed' in h_data.keys():
                                sequence_weather.his_hourly_wind_speed = h_data['wind_speed']
                            if 'wind_degree' in h_data.keys():
                                sequence_weather.his_hourly_wind_degree = h_data['wind_degree']
                            if 'wind_dir' in h_data.keys():
                                sequence_weather.his_hourly_wind_dir = h_data['wind_dir']
                            if 'weather_code' in h_data.keys():
                                sequence_weather.his_hourly_weather_code = h_data['weather_code']
                            if 'weather_icons' in h_data.keys():
                                sequence_weather.his_hourly_weather_icons = h_data['weather_icons']
                            if 'weather_descriptions' in h_data.keys():
                                sequence_weather.his_hourly_weather_descriptions = h_data['weather_descriptions']
                            if 'precip' in h_data.keys():
                                sequence_weather.his_hourly_precip = h_data['precip']
                            if 'humidity' in h_data.keys():
                                sequence_weather.his_hourly_humidity = h_data['humidity']
                            if 'visibility' in h_data.keys():
                                sequence_weather.his_hourly_visibility = h_data['visibility']
                            if 'pressure' in h_data.keys():
                                sequence_weather.his_hourly_pressure = h_data['pressure']
                            if 'cloudcover' in h_data.keys():
                                sequence_weather.his_hourly_cloudcover = h_data['cloudcover']
                            if 'heatindex' in h_data.keys():
                                sequence_weather.his_hourly_heatindex = h_data['heatindex']
                            if 'dewpoint' in h_data.keys():
                                sequence_weather.his_hourly_dewpoint = h_data['dewpoint']
                            if 'windchill' in h_data.keys():
                                sequence_weather.his_hourly_windchill = h_data['windchill']
                            if 'windgust' in h_data.keys():
                                sequence_weather.his_hourly_windgust = h_data['windgust']
                            if 'feelslike' in h_data.keys():
                                sequence_weather.his_hourly_feelslike = h_data['feelslike']
                            if 'chanceofrain' in h_data.keys():
                                sequence_weather.his_hourly_chanceofrain = h_data['chanceofrain']
                            if 'chanceofremdry' in h_data.keys():
                                sequence_weather.his_hourly_chanceofremdry = h_data['chanceofremdry']
                            if 'chanceofwindy' in h_data.keys():
                                sequence_weather.his_hourly_chanceofwindy = h_data['chanceofwindy']
                            if 'chanceofovercast' in h_data.keys():
                                sequence_weather.his_hourly_chanceofovercast = h_data['chanceofovercast']
                            if 'chanceofsunshine' in h_data.keys():
                                sequence_weather.his_hourly_chanceofsunshine = h_data['chanceofsunshine']
                            if 'chanceoffrost' in h_data.keys():
                                sequence_weather.his_hourly_chanceoffrost = h_data['chanceoffrost']
                            if 'chanceofhightemp' in h_data.keys():
                                sequence_weather.his_hourly_chanceofhightemp = h_data['chanceofhightemp']
                            if 'chanceoffog' in h_data.keys():
                                sequence_weather.his_hourly_chanceoffog = h_data['chanceoffog']
                            if 'chanceofsnow' in h_data.keys():
                                sequence_weather.his_hourly_chanceofsnow = h_data['chanceofsnow']
                            if 'chanceofthunder' in h_data.keys():
                                sequence_weather.his_hourly_chanceofthunder = h_data['chanceofthunder']
                            if 'uv_index' in h_data.keys():
                                sequence_weather.his_hourly_ = h_data['uv_index']

            sequence_weather.save()
            return True
    return False

def get_images_by_sequence(sequence, source=None, token=None, image_insert=True, image_download=True, is_weather=True):
    if is_weather and not sequence.getFirstPointLat() is None and not sequence.getFirstPointLng() is None:
        print(save_weather(sequence))

    if token is None:
        token = sequence.user.mapillary_access_token
    mapillary = Mapillary(token, source=source)
    image_json = mapillary.get_images_with_ele_by_seq_key([sequence.seq_key])
    if image_json and image_insert:
        image_features = image_json['features']
        print('Images insert!')

        image_keys = []
        image_position_ary = []
        for image_feature in image_features:
            images = Image.objects.filter(image_key=image_feature['properties']['key'])
            print(image_feature)
            print(image_feature['properties']['altitude'])
            if images.count() > 0:
                image = images[0]
                continue
            else:
                image = Image()
            image_keys.append(image_feature['properties']['key'])
            image_position_ary.append(image_feature['geometry']['coordinates'])

            image.user = sequence.user
            image.sequence = sequence

            if 'ca' in image_feature['properties'].keys():
                image.cas = image_feature['properties']['ca']
            if 'altitude' in image_feature['properties'].keys():
                image.ele = image_feature['properties']['altitude']
            if 'camera_make' in image_feature['properties'].keys() and image_feature['properties']['camera_make'] != '':
                camera_make_str = image_feature['properties']['camera_make']
                camera_makes = CameraMake.objects.filter(name=camera_make_str)
                if camera_makes.count() == 0:
                    camera_make = CameraMake()
                    camera_make.name = camera_make_str
                    camera_make.save()
                else:
                    camera_make = camera_makes[0]
                image.camera_make = camera_make
            if 'camera_model' in image_feature['properties'].keys() and image_feature['properties']['camera_model'] != '':
                camera_model_str = image_feature['properties']['camera_model']
                camera_models = CameraModel.objects.filter(name=camera_model_str)
                if camera_models.count() == 0:
                    camera_model = CameraModel()
                    camera_model.name = camera_model_str
                    camera_model.save()
                else:
                    camera_model = camera_models[0]
                image.camera_model = camera_model
            if 'key' in image_feature['properties'].keys():
                image.image_key = image_feature['properties']['key']
            if 'pano' in image_feature['properties'].keys():
                image.pano = image_feature['properties']['pano']
            if 'sequence_key' in image_feature['properties'].keys():
                image.seq_key = image_feature['properties']['sequence_key']
            if 'user_key' in image_feature['properties'].keys():
                image.user_key = image_feature['properties']['user_key']
            if 'username' in image_feature['properties'].keys():
                image.username = image_feature['properties']['username']
            if 'organization_key' in image_feature['properties'].keys():
                image.organization_key = image_feature['properties']['organization_key']
            if 'private' in image_feature['properties'].keys():
                image.private = image_feature['properties']['private']
            if 'captured_at' in image_feature['properties'].keys():
                image.captured_at = image_feature['properties']['captured_at']

            image.lat = image_feature['geometry']['coordinates'][0]
            image.lng = image_feature['geometry']['coordinates'][1]

            image.point = Point(image.lat, image.lng)
            image.save()
            print('image key: ', image.image_key)

        print(image_keys)
        print(image_download)
        if len(image_keys) > 0 and image_download:
            # Create the model you want to save the image to
            for image_key in image_keys:
                images = Image.objects.filter(image_key=image_key)
                if images.count() == 0:
                    print('image_count: ', images.count())
                    continue
                if not images[0].mapillary_image is None and images[0].mapillary_image != '':
                    print(images[0].mapillary_image)
                    print('mapillary_image is not none')
                    continue
                image = images[0]

                lf = mapillary.download_mapillary_image(image.image_key)
                # Save the temporary image to the model#
                # This saves the model so be sure that is it valid
                if lf:
                    image.mapillary_image.save(image.image_key, files.File(lf))
                    image.save()
                    print(image.mapillary_image)

        if image_insert:
            sequence.is_published = True
            sequence.save()
    return image_json

def set_camera_make(sequence):
    if sequence.camera_make is None or sequence.camera_make == '':
        return False
    camera_makes = CameraMake.objects.filter(name=sequence.camera_make)
    if camera_makes.count() == 0:
        camera_make = CameraMake()
        camera_make.name = sequence.camera_make
        camera_make.save()
        return True
    else:
        return False

def sequence_detail(request, unique_id):
    sequence = get_object_or_404(Sequence, unique_id=unique_id)
    print('1')
    p = threading.Thread(target=get_images_by_sequence, args=(sequence,))
    p.start()
    print('2')
    set_camera_make(sequence)

    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        image_key = request.GET.get('image_key')
        if page is None:
            page = 1

        view_mode = request.GET.get('view_mode')
        if view_mode is None:
            view_mode = 'original'


    geometry_coordinates_ary = sequence.geometry_coordinates_ary
    coordinates_image = sequence.coordinates_image
    coordinates_cas = sequence.coordinates_cas

    images = []

    for i in range(len(coordinates_image)):
        images.append(
            {
                'lat': geometry_coordinates_ary[i][0],
                'lng': geometry_coordinates_ary[i][1],
                'key': coordinates_image[i],
                'cas': coordinates_cas[i]
            }
        )

    view_points = 0
    imgs = Image.objects.filter(image_key=coordinates_image[0])
    if imgs.count() > 0:
        i_vs = ImageViewPoint.objects.filter(image=imgs[0])
        view_points = i_vs.count()

    addSequenceForm = AddSequeceForm(instance=sequence)

    label_types = LabelType.objects.filter(parent__isnull=False)
    tours = TourSequence.objects.filter(sequence=sequence)
    tour_count = tours.count()
    sequence_weathers = SequenceWeather.objects.filter(sequence=sequence)
    sequence_weather = None
    if sequence_weathers.count() > 0:
        sequence_weather = sequence_weathers[0]
    print(sequence_weather)
    content = {
        'sequence': sequence,
        'pageName': 'Sequence Detail',
        'pageTitle': sequence.name + ' - Sequence',
        'pageDescription': sequence.description,
        'first_image': images[0],
        'page': page,
        'view_points': view_points,
        'addSequenceForm': addSequenceForm,
        'label_types': label_types,
        'image_key': image_key,
        'tour_count': tour_count,
        'sequence_weather': sequence_weather,
        'view_mode': view_mode
    }
    return render(request, 'sequence/detail.html', content)

@my_login_required
def sequence_delete(request, unique_id):
    sequence = get_object_or_404(Sequence, unique_id=unique_id)
    if request.method == "POST":
        if sequence.user != request.user:
            messages.error(request, 'The sequence does not exist or has no access.')
            return redirect('sequence.index')
        name = sequence.name
        sequence.name = ''
        sequence.description = ''
        sequence.transport_type = None
        tags = sequence.tag.all()
        for tag in tags:
            sequence.tag.remove(tag)
        sequence.is_published = False
        sequence.save()

        seq_likes = SequenceLike.objects.filter(sequence=sequence)

        if seq_likes.count() > 0:
            for s in seq_likes:
                s.delete()

        tour_sequences = TourSequence.objects.filter(sequence=sequence)

        if tour_sequences.count() > 0:
            for t_seq in tour_sequences:
                t_seq.delete()

        messages.success(request, '"{}" is deleted successfully.'.format(name))
        return redirect('sequence.index')

    messages.error(request, 'The sequence does not exist or has no access.')
    return redirect('sequence.index')

def ajax_save_sequence(request, unique_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist or has no access.'
        })
    if request.method == "POST":
        form = AddSequeceForm(request.POST)

        if form.is_valid():
            sequence = Sequence.objects.get(unique_id=unique_id)

            if not sequence or sequence is None or sequence.user != request.user:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The Sequence does not exist or has no access.'
                })

            sequence.name = form.cleaned_data['name']
            sequence.description = form.cleaned_data['description']
            sequence.transport_type = form.cleaned_data['transport_type']
            if form.cleaned_data['tag'].count() > 0:
                for tag in form.cleaned_data['tag']:
                    sequence.tag.add(tag)
                for tag in sequence.tag.all():
                    if not tag in form.cleaned_data['tag']:
                        sequence.tag.remove(tag)
            sequence.save()

            tags = []
            if sequence.tag.all().count() > 0:
                for tag in sequence.tag.all():
                    if not tag or tag is None:
                        continue
                    tags.append(tag.name)

            transport_parent_html = render_to_string(
                'sequence/transport_parent_box.html',
                {'sequence': sequence},
                request
            )

            transport_html = render_to_string(
                'sequence/transport_box.html',
                {'sequence': sequence},
                request
            )


            return JsonResponse({
                'status': 'success',
                'message': 'This sequence is updated successfully.',
                'sequence': {
                    'name': sequence.name,
                    'description': sequence.description,
                    'transport_type': sequence.transport_type.name,
                    'transport_parent_html': transport_parent_html,
                    'transport_html': transport_html,
                    'tags': tags
                }
            })
        else:
            errors = []
            for field in form:
                for error in field.errors:
                    errors.append(field.name + ': ' + error)
            return JsonResponse({
                'status': 'failed',
                'message': '<br>'.join(errors)
            })
    return JsonResponse({
        'status': 'failed',
        'message': 'The sequence does not exist or has no access.'
    })

def sort_by_captured_at(item):
    return str(item['properties']['captured_at'])

@my_login_required
def import_sequence_list(request):
    sequences = []
    search_form = TransportSearchForm()
    action = 'filter'
    if request.method == "GET":
        month = request.GET.get('month')
        page = request.GET.get('page')
        action = request.GET.get('action')
        if action is None:
            action = 'filter'

        if not month is None:
            search_form.set_month(month)

            y = month.split('-')[0]
            m = month.split('-')[1]

            map_users = MapillaryUser.objects.filter(user=request.user)
            if map_users.count() == 0:
                return redirect('home')
            else:
                map_user = map_users[0]

            if page is None:
                start_time = month + '-01'

                if m == '12':
                    y = str(int(y) + 1)
                    m = '01'
                else:
                    if int(m) < 9:
                        m = '0' + str(int(m) + 1)
                    else:
                        m = str(int(m) + 1)
                end_time = y + '-' + m + '-01'
                per_page = 1000

                url = 'https://a.mapillary.com/v3/sequences?page=1&per_page={}&client_id={}&userkeys={}&start_time={}&end_time={}'.format(
                    per_page,
                    settings.MAPILLARY_CLIENT_ID,
                    map_user.key,
                    start_time,
                    end_time
                )
                response = requests.get(url)
                data = response.json()
                features = data['features']
                features.sort(key=sort_by_captured_at)
                request.session['sequences'] = features

                page = 1
            if request.session['sequences'] is None or not request.session['sequences']:
                request.session['sequences'] = []

            sequences_ary = []

            for seq in request.session['sequences']:
                seq_s = Sequence.objects.filter(seq_key=seq['properties']['key'])[:1]
                if seq_s.count() == 0:
                    sequences_ary.append(seq)

            paginator = Paginator(sequences_ary, 5)
            try:
                sequences = paginator.page(page)
            except PageNotAnInteger:
                sequences = paginator.page(1)
            except EmptyPage:
                sequences = paginator.page(paginator.num_pages)

            first_num = 1
            last_num = paginator.num_pages
            if paginator.num_pages > 7:
                if sequences.number < 4:
                    first_num = 1
                    last_num = 7
                elif sequences.number > paginator.num_pages - 3:
                    first_num = paginator.num_pages - 6
                    last_num = paginator.num_pages
                else:
                    first_num = sequences.number - 3
                    last_num = sequences.number + 3
            sequences.paginator.pages = range(first_num, last_num + 1)
            sequences.count = len(sequences)

            for i in range(len(sequences)):
                seq = Sequence.objects.filter(seq_key=sequences[i]['properties']['key'])[:1]
                if seq.count() > 0:
                    sequences[i]['unique_id'] = str(seq[0].unique_id)
                    sequences[i]['name'] = seq[0].name
                    sequences[i]['description'] = seq[0].description
                    if seq[0].transport_type is None:
                        sequences[i]['transport_type'] = ''
                    else:
                        sequences[i]['transport_type'] = seq[0].transport_type.parent.name + ' - ' +seq[0].transport_type.name
                    sequences[i]['tags'] = seq[0].getTags()
                else:
                    sequences[i]['unique_id'] = None

                sequences[i]['image_count'] = len(sequences[i]['properties']['coordinateProperties']['image_keys'])
                sequences[i]['captured_at'] = sequences[i]['properties']['captured_at']
                sequences[i]['camera_make'] = sequences[i]['properties']['camera_make']
                sequences[i]['created_at'] = sequences[i]['properties']['created_at']
                sequences[i]['seq_key'] = sequences[i]['properties']['key']
                sequences[i]['pano'] = sequences[i]['properties']['pano']
                sequences[i]['user_key'] = sequences[i]['properties']['user_key']
                sequences[i]['username'] = sequences[i]['properties']['username']
                sequences[i]['geometry_coordinates_ary'] = sequences[i]['geometry']['coordinates']


    addSequenceForm = AddSequeceForm()

    all_transport_types = []
    transport_types = TransType.objects.all()
    for type in transport_types:
        all_transport_types.append({'id': type.pk, 'name': type.name})
    content = {
        'search_form': search_form,
        'seq_count': len(sequences),
        'sequences': sequences,
        'pageName': 'Sequences',
        'pageTitle': 'Import Sequences',
        'pageDescription': IMPORT_PAGE_DESCRIPTION,
        'addSequenceForm': addSequenceForm,
        'all_transport_types': all_transport_types,
        'action': action,
        'page': page
    }
    return render(request, 'sequence/import_list.html', content)

@my_login_required
def ajax_import(request, seq_key):
    if request.method == 'POST':

        # form = AddSequeceForm(request.POST)
        # if form.is_valid():
        # for unique_id in sequence_json.keys():
        #     sequence = Sequence.objects.get(unique_id=unique_id)
        #     if sequence is None:
        #         continue
        #     if sequence_json[unique_id]['name'] == '' or sequence_json[unique_id]['description'] == '' or sequence_json[unique_id]['transport_type'] == 0 or len(sequence_json[unique_id]['tags']) == 0:
        #         continue
        form = AddSequeceForm(request.POST)
        if form.is_valid():

            # for i in range(len(request.session['sequences'])):
            for feature in request.session['sequences']:
                # feature = request.session['sequences'][i]
                if feature['properties']['key'] == seq_key:
                    properties = feature['properties']
                    geometry = feature['geometry']
                    sequence = Sequence.objects.filter(seq_key=seq_key)[:1]

                    if sequence.count() > 0:
                        continue
                    else:
                        sequence = Sequence()
                    sequence.user = request.user
                    if 'camera_make' in properties and properties['camera_make'] != '':
                        camera_makes = CameraMake.objects.filter(name=properties['camera_make'])
                        if camera_makes.count() > 0:
                            c = camera_makes[0]
                        else:
                            c = CameraMake()
                            c.name = properties['camera_make']
                            c.save()
                        sequence.camera_make = c

                    sequence.captured_at = properties['captured_at']
                    if 'created_at' in properties:
                        sequence.created_at = properties['created_at']
                    sequence.seq_key = properties['key']
                    if 'pano' in properties:
                        sequence.pano = properties['pano']
                    if 'user_key' in properties:
                        sequence.user_key = properties['user_key']
                    if 'username' in properties:
                        sequence.username = properties['username']
                    sequence.geometry_coordinates_ary = geometry['coordinates']
                    sequence.image_count = len(geometry['coordinates'])

                    sequence.geometry_coordinates = LineString(sequence.geometry_coordinates_ary)

                    sequence.coordinates_cas = properties['coordinateProperties']['cas']
                    sequence.coordinates_image = properties['coordinateProperties']['image_keys']
                    if 'private' in properties:
                        sequence.is_privated = properties['private']

                    sequence.name = form.cleaned_data['name']
                    sequence.description = form.cleaned_data['description']
                    sequence.transport_type = form.cleaned_data['transport_type']
                    sequence.is_published = True
                    sequence.save()

                    sequence.distance = sequence.getDistance()
                    sequence.save()

                    set_camera_make(sequence)

                    if form.cleaned_data['tag'].count() > 0:
                        for tag in form.cleaned_data['tag']:
                            sequence.tag.add(tag)
                        for tag in sequence.tag.all():
                            if not tag in form.cleaned_data['tag']:
                                sequence.tag.remove(tag)

                    # get image data from mapillary with sequence_key
                    print('1')
                    p = threading.Thread(target=get_images_by_sequence, args=(sequence,))
                    p.start()
                    print('2')
                    # messages.success(request, "Sequences successfully imported.")
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Sequence successfully imported. Sequence will be published in about 30 minutes.',
                        'unique_id': str(sequence.unique_id)
                    })
        else:
            errors = []
            for field in form:
                for error in field.errors:
                    errors.append(field.name + ': ' + error)
            return JsonResponse({
                'status': 'failed',
                'message': '<br>'.join(errors)
            })
    return JsonResponse({
        'status': 'failed',
        'message': 'Sequence was not imported.'
    })

def ajax_sequence_check_publish(request, unique_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't change the status."
        })

    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The sequence does not exist.'
        })

    if sequence.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'This sequence is not created by you.'
        })

    if sequence.is_published:
        sequence.is_published = False
        message = 'Unpublished'
    else:
        sequence.is_published = True
        message = 'Published'
    sequence.save()
    return JsonResponse({
        'status': 'success',
        'message': message,
        'is_published': sequence.is_published
    })

def ajax_sequence_check_like(request, unique_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't change the status."
        })

    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The sequence does not exist.'
        })

    if sequence.user == request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'This sequence is created by you.'
        })

    sequence_like = SequenceLike.objects.filter(sequence=sequence, user=request.user)
    if sequence_like:
        for g in sequence_like:
            g.delete()
        liked_sequence = SequenceLike.objects.filter(sequence=sequence)
        if not liked_sequence:
            liked_count = 0
        else:
            liked_count = liked_sequence.count()
        return JsonResponse({
            'status': 'success',
            'message': 'Unliked',
            'is_checked': False,
            'liked_count': liked_count
        })
    else:
        sequence_like = SequenceLike()
        sequence_like.sequence = sequence
        sequence_like.user = request.user
        sequence_like.save()
        liked_sequence = SequenceLike.objects.filter(sequence=sequence)
        if not liked_sequence:
            liked_count = 0
        else:
            liked_count = liked_sequence.count()
        return JsonResponse({
            'status': 'success',
            'message': 'Liked',
            'is_checked': True,
            'liked_count': liked_count
        })

def ajax_get_image_detail(request, unique_id, image_key):
    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    if not sequence.is_published:
        if not request.user.is_authenticated or request.user != sequence.user:
            return JsonResponse({
                'status': 'failed',
                'message': "You can't access this sequence."
            })
    images = Image.objects.filter(image_key=image_key)[:1]
    if images.count() > 0:
        image = images[0]
    else:
        return JsonResponse({
            'status': 'failed',
            'message': "The image doesn't exist.",
        })

    view_points = ImageViewPoint.objects.filter(image=image)
    scenes = Scene.objects.filter(image_key=image_key)
    content = {
        'image': image,
        'view_points': view_points.count(),
        'guidebook_count': scenes.count(),
        'sequence': sequence
    }
    image_detail_box_html = render_to_string(
        'sequence/image_detail_box.html',
        content,
        request
    )
    return JsonResponse({
        'image_detail_box_html': image_detail_box_html,
        'status': 'success',
        'message': "",
        'view_points': view_points.count()
    })

def ajax_delete_image_label(request, unique_id, image_key):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': 'You are required login.'
        })

    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    if not sequence.is_published:
        if not request.user.is_authenticated or request.user != sequence.user:
            return JsonResponse({
                'status': 'failed',
                'message': "You can't access this sequence."
            })

    images = Image.objects.filter(sequence=sequence, image_key=image_key)[:1]

    if images.count() == 0:
        return JsonResponse({
            'status': 'failed',
            'message': "The image doesn't exist.",
        })
    else:
        image = images[0]

    if request.method == 'POST':
        label_id = request.POST.get('label_id')
        if not label_id or label_id is None:
            return JsonResponse({
                'status': 'failed',
                'message': "label_id is required.",
            })

        image_labels = ImageLabel.objects.filter(user=request.user, image=image, unique_id=label_id)[:1]
        if image_labels.count() > 0:
            image_label = image_labels[0]
            image_label.delete()
            return JsonResponse({
                'status': 'success',
                'message': "Image label is successfully deleted.",
            })
    return JsonResponse({
        'status': 'failed',
        'message': "The image label doesn't exist.",
    })

def ajax_get_image_label(request, unique_id, image_key):
    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    if not sequence.is_published:
        if not request.user.is_authenticated or request.user != sequence.user:
            return JsonResponse({
                'status': 'failed',
                'message': "You can't access this sequence."
            })

    images = Image.objects.filter(sequence=sequence, image_key=image_key)[:1]

    if images.count() == 0:
        return JsonResponse({
            'status': 'failed',
            'message': "The image doesn't exist.",
        })
    else:
        image = images[0]

    image_labels = ImageLabel.objects.filter(image=image)
    image_label_ary = []
    if image_labels.count() > 0:
        for image_label in image_labels:
            if image_label.user == request.user:
                is_mine = True
            else:
                is_mine = False
            geometry = None
            geo_type = None
            if not image_label.point is None:
                geometry = image_label.point.coords
                geo_type = 'point'
            elif not image_label.polygon is None:
                geometry = image_label.polygon.coords[0]
                geo_type = 'polygon'
            image_label_json = {
                'label_id': str(image_label.unique_id),
                'is_mine': is_mine,
                'image_key': image_key,
                'geometry': geometry,
                'geo_type': geo_type,
                'label_type_key': image_label.label_type.getKey(),
                'label_type_color': image_label.label_type.color
            }
            image_label_ary.append(image_label_json)
    return JsonResponse({
        'status': 'success',
        'data': {
            'image_labels': image_label_ary
        },
        'message': 'A new label is successfully added.'
    })

def ajax_add_label_type(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': 'You are required login.'
        })
    if request.method == 'POST':
        label_type_keys = request.POST.get('keys')
        if not label_type_keys is None and label_type_keys != '':
            label_types = label_type_keys.split(',')
            if len(label_types) > 0:
                for label_type in label_types:
                    l_ary = label_type.split('--')
                    index = 0
                    if (len(l_ary) > 0):
                        l_type = None
                        for l in l_ary:
                            if index == 0:
                                types = LabelType.objects.filter(parent__isnull=True, name=l)
                            else:
                                types = LabelType.objects.filter(parent=l_type, name=l)
                            if types.count() == 0:
                                l_parent_type = l_type
                                l_type = LabelType()
                                l_type.name = l
                                l_type.source = 'mapillary'
                                l_type.parent = l_parent_type
                                print(l_type.name)
                                l_type.save()
                            else:
                                l_type = types[0]
                            index += 1

        label_types_json = {}
        label_types = LabelType.objects.filter(source='mapillary')
        if label_types.count() > 0:
            for label_type in label_types:
                label_types_json[label_type.getKey()] = label_type.color

        return JsonResponse({
            'status': 'success',
            'message': 'label types updated.',
            'data': {
                'label_types_json': label_types_json
            }
        })
    return JsonResponse({
        'status': 'failed',
        'message': 'You are required login.'
    })

def ajax_add_image_label(request, unique_id, image_key):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': 'You are required login.'
        })

    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    if not sequence.is_published:
        if not request.user.is_authenticated or request.user != sequence.user:
            return JsonResponse({
                'status': 'failed',
                'message': "You can't access this sequence."
            })

    images = Image.objects.filter(sequence=sequence, image_key=image_key)[:1]

    if images.count() == 0:
        return JsonResponse({
            'status': 'failed',
            'message': "The image doesn't exist.",
        })
    else:
        image = images[0]

    if request.method == 'POST':
        geometry_str = request.POST.get('geometry')
        geometry = json.loads(geometry_str)
        label_id = request.POST.get('label_type')
        geo_type = request.POST.get('geo_type')
        print(label_id)
        label_types = LabelType.objects.filter(pk=label_id)[:1]
        if label_types.count() == 0:
            return JsonResponse({
                'status': 'failed',
                'message': 'The label type does not exist.'
            })
        else:
            label_type = label_types[0]
        print(geometry)
        image_label = ImageLabel()
        image_label.image = image
        image_label.user = request.user
        image_label.label_type = label_type
        if geo_type == 'point' and label_type.type == 'point':
            image_label.point = Point(geometry)
            image_label.save()
        elif geo_type == 'polygon' and label_type.type == 'polygon':
            image_label.polygon = Polygon(geometry)
            image_label.save()
        return JsonResponse({
            'status': 'success',
            'data': {
                'label_id': str(image_label.unique_id),
                'label_type_key': image_label.label_type.getKey(),
                'label_type_color': image_label.label_type.color
            },
            'message': 'Label added successfully'
        })

def ajax_get_image_list(request, unique_id):
    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    if not sequence.is_published:
        if not request.user.is_authenticated or request.user != sequence.user:
            return JsonResponse({
                'status': 'failed',
                'message': "You can't access this sequence."
            })

    geometry_coordinates_ary = sequence.geometry_coordinates_ary
    coordinates_image = sequence.coordinates_image
    coordinates_cas = sequence.coordinates_cas

    images = []

    for i in range(len(coordinates_image)):
        images.append(
            {
                'lat': geometry_coordinates_ary[i][1],
                'lng': geometry_coordinates_ary[i][0],
                'key': coordinates_image[i],
                'cas': coordinates_cas[i]
            }
        )

    page = 1
    image_key = None
    if request.method == "GET":
        page = request.GET.get('page')
        image_key = request.GET.get('image_key')
        if page is None:
            page = 1
    image_in_page = None
    if not image_key is None and len(images) > 0:
        for index in range(len(images)):
            image = images[index]
            if image_key == image['key']:
                image_in_page = int(index / 20) + 1
                print('image_in_page: ', image_in_page)
                break

    if not image_in_page is None:
        page = image_in_page
    else:
        image_key = None
    print('page: ', page)
    paginator = Paginator(images, 20)


    try:
        pImages = paginator.page(page)
    except PageNotAnInteger:
        pImages = paginator.page(1)
    except EmptyPage:
        pImages = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pImages.number < 4:
            first_num = 1
            last_num = 7
        elif pImages.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pImages.number - 3
            last_num = pImages.number + 3
    pImages.paginator.pages = range(first_num, last_num + 1)
    pImages.count = len(pImages)
    origin_images = []
    for i in range(pImages.count):
        image = Image.objects.filter(image_key=pImages[i]['key'])[:1]
        if image.count() == 0:
            origin_images.append(None)
        else:
            origin_images.append(image[0])

            view_points = ImageViewPoint.objects.filter(image=image[0])
            scenes = Scene.objects.filter(image_key=image[0].image_key)
            pImages[i]['view_points'] = view_points.count()
            pImages[i]['guidebooks'] = scenes.count()

    addSequenceForm = AddSequeceForm(instance=sequence)

    content = {
        'sequence': sequence,
        'images': pImages,
        'origin_images': origin_images,
        'pageName': 'Sequence Detail',
        'pageTitle': sequence.name + ' - Sequence',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page,
        'first_image': pImages[0],
        'addSequenceForm': addSequenceForm,
        'image_key': image_key
    }

    image_list_box_html = render_to_string(
        'sequence/image_list_box.html',
        content,
        request
    )

    return JsonResponse({
        'image_list_box_html': image_list_box_html,
        'page': page,
        'image_key': image_key,
        'status': 'success',
        'message': ''
    })

def ajax_image_mark_view(request, unique_id, image_key):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't change the status."
        })

    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    if sequence.user == request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'The sequence and image are imported by you.'
        })

    if not sequence.is_published:
        if not request.user.is_authenticated or request.user != sequence.user:
            return JsonResponse({
                'status': 'failed',
                'message': "You can't access this sequence."
            })

    images = Image.objects.filter(seq_key=sequence.seq_key, image_key=image_key)

    if images.count() == 0:
        return JsonResponse({
            'status': 'failed',
            'message': "The Image does not exist."
        })

    image = images[0]

    image_view_points = ImageViewPoint.objects.filter(image=image, user=request.user)
    if image_view_points.count() > 0:
        for v in image_view_points:
            v.delete()
        marked_images = ImageViewPoint.objects.filter(image=image)
        if not marked_images:
            view_points = 0
        else:
            view_points = marked_images.count()
        return JsonResponse({
            'status': 'success',
            'message': 'Unmarked',
            'is_marked': False,
            'view_points': view_points
        })
    else:
        image_view_point = ImageViewPoint()
        image_view_point.image = image
        image_view_point.user = request.user
        image_view_point.owner = image.sequence.user
        image_view_point.save()
        marked_images = ImageViewPoint.objects.filter(image=image)
        if not marked_images:
            view_points = 0
        else:
            view_points = marked_images.count()
        return JsonResponse({

            'status': 'success',
            'message': 'Marked',
            'is_marked': True,
            'view_points': view_points
        })

def ajax_get_image_ele(request, unique_id):
    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    if not sequence.is_published:
        if not request.user.is_authenticated or request.user != sequence.user:
            return JsonResponse({
                'status': 'failed',
                'message': "You can't access this sequence."
            })

    images = Image.objects.filter(sequence=sequence).order_by('captured_at')

    ele_ary = []

    if images.count() > 0:
        for image in images:
            if image.ele is None:
                ele_ary.append(0)
            else:
                ele_ary.append(image.ele)


    return JsonResponse({
        'status': 'success',
        'message': '',
        'eles': ele_ary
    })

def ajax_get_detail(request, unique_id):
    sequence = Sequence.objects.get(unique_id=unique_id)
    if sequence.user == request.user:
        is_mine = True
    else:
        is_mine = False
    serialized_obj = serializers.serialize('json', [sequence, ])
    data = {
        'sequence': json.loads(serialized_obj)
    }

    if not data['sequence']:
        data['message'] = "The sequence id doesn't exist."
    else:
        data['sequence_html_detail'] = render_to_string('sequence/modal_detail.html', {'sequence': sequence, 'is_mine': is_mine})

    return JsonResponse(data)
