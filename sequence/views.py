# Python packages
import json
import threading

from django.contrib import messages
from django.contrib.gis.geos import Point, Polygon, LineString
from django.core import files
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.db.models.expressions import Window
from django.db.models.functions.window import RowNumber
from django.http import (
    JsonResponse, )
# Django Packages
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.db import connection
# Project packages
from accounts.models import CustomUser, MapillaryUser
from challenge.models import Challenge, LabelChallenge
from guidebook.models import Guidebook, Scene
from tour.models import TourSequence, Tour
# Custom Libs ##
from lib.mapillary import Mapillary
from lib.weatherstack import WeatherStack
from lib.django_db_functions import get_correct_sql
# That includes from .models import *
from .forms import *

# App packages

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
    order_type = 'latest_at'
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        order_type = request.GET.get('order_type')
        form = SequenceSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            camera_makes = form.cleaned_data['camera_make']
            tags = form.cleaned_data['tag']
            transport_type = form.cleaned_data['transport_type']
            username = form.cleaned_data['username']
            like = form.cleaned_data['like']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            pano = form.cleaned_data['pano']

            sequences = Sequence.objects.all().filter(
                is_published=True
            ).exclude(image_count=0)
            if name and name != '':
                sequences = sequences.filter(name__icontains=name)
            if camera_makes is not None and len(camera_makes) > 0:
                sequences = sequences.filter(camera_make__name__in=camera_makes)
            if transport_type is not None and transport_type != 'all' and transport_type != '':
                transport_type_obj = TransType.objects.filter(name=transport_type).first()
                if transport_type_obj is not None:
                    children_trans_type = TransType.objects.filter(parent=transport_type_obj)
                    if children_trans_type.count() > 0:
                        types = [transport_type_obj]
                        for t in children_trans_type:
                            types.append(t)
                        sequences = sequences.filter(transport_type__in=types)
                    else:
                        sequences = sequences.filter(transport_type=transport_type_obj)
            if username and username != '':
                users = CustomUser.objects.filter(username__icontains=username)
                sequences = sequences.filter(user__in=users)
            if len(tags) > 0:
                for tag in tags:
                    sequences = sequences.filter(tag=tag)
            if like and like != 'all':
                sequence_likes = SequenceLike.objects.all().values('sequence').annotate()
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
                    sequences = sequences.filter(
                        captured_at__month=m,
                        captured_at__year=y
                    )

                elif time_type == 'yearly':
                    if filter_time is None or filter_time == '':
                        now = datetime.now()
                        y = now.year
                    else:
                        y = filter_time
                    sequences = sequences.filter(
                        captured_at__year=y
                    )

            challenge_id = request.GET.get('challenge_id')
            if challenge_id is not None and challenge_id != '':
                challenges = Challenge.objects.filter(unique_id=challenge_id)
                if challenges.count() > 0:
                    challenge = challenges[0]
                    sequences = sequences.filter(geometry_coordinates__intersects=challenge.multipolygon)

            if start_time is not None and start_time != '':
                sequences = sequences.filter(captured_at__gte=start_time)

            if end_time is not None and end_time != '':
                sequences = sequences.filter(captured_at__lte=end_time)

            if pano is not None and pano != '' and pano != 'all':
                if pano == 'true':
                    sequences = sequences.filter(pano=True)
                elif pano == 'false':
                    sequences = sequences.filter(pano=False)

    if sequences is None:
        sequences = Sequence.objects.all().filter(is_published=True).exclude(image_count=0)
        form = SequenceSearchForm()

    request.session['sequences_query'] = get_correct_sql(sequences)
    if order_type == 'most_likes':
        paginator = Paginator(sequences.order_by('-like_count', '-captured_at'), 10)
    else:
        paginator = Paginator(sequences.order_by('-captured_at'), 10)

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
        'page': page,
        'order_type': order_type
    }
    return render(request, 'sequence/list.html', content)


@my_login_required
def my_sequence_list(request):
    sequences = None
    page = 1
    order_type = 'latest_at'
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        order_type = request.GET.get('order_type')
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
                sequences = sequences.filter(name__icontains=name)
            if camera_makes is not None and len(camera_makes) > 0:
                sequences = sequences.filter(camera_make__name__in=camera_makes)
            if transport_type is not None and transport_type != 'all' and transport_type != '':
                transport_type_obj = TransType.objects.filter(name=transport_type).first()
                if transport_type_obj is not None:
                    children_trans_type = TransType.objects.filter(parent=transport_type_obj)
                    if children_trans_type.count() > 0:
                        types = [transport_type_obj]
                        for t in children_trans_type:
                            types.append(t)
                        sequences = sequences.filter(transport_type__in=types)
                    else:
                        sequences = sequences.filter(transport_type=transport_type_obj)
            if len(tags) > 0:
                for tag in tags:
                    sequences = sequences.filter(tag=tag)
            if like and like != 'all':
                sequence_likes = SequenceLike.objects.all().values('sequence').annotate()
                sequence_ary = []
                if sequence_likes.count() > 0:
                    for sequence_like in sequence_likes:
                        sequence_ary.append(sequence_like['sequence'])
                if like == 'true':
                    sequences = sequences.filter(pk__in=sequence_ary)
                elif like == 'false':
                    sequences = sequences.exclude(pk__in=sequence_ary)

    if sequences is None:
        sequences = Sequence.objects.all().filter(is_published=True).exclude(image_count=0)
        form = SequenceSearchForm()

    request.session['sequences_query'] = get_correct_sql(sequences)

    if order_type == 'most_likes':
        paginator = Paginator(sequences.order_by('-like_count', '-captured_at'), 10)
    else:
        paginator = Paginator(sequences.order_by('-captured_at'), 10)

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
        'page': page,
        'order_type': order_type
    }
    return render(request, 'sequence/list.html', content)


def image_leaderboard(request):
    images = None
    page = 1
    image_view_points = ImageViewPoint.objects.filter()
    label_challenges = LabelChallenge.objects.filter()
    filter_type = None

    if request.method == "GET":
        page = request.GET.get('page')
        filter_type = request.GET.get('filter_type')
        if page is None:
            page = 1
        form = ImageSearchForm(request.GET)
        if form.is_valid():

            username = form.cleaned_data['username']
            camera_makes = form.cleaned_data['camera_make']
            transport_type = form.cleaned_data['transport_type']
            map_feature_value = form.cleaned_data['map_feature']

            images = Image.objects.all()

            if camera_makes is not None and len(camera_makes) > 0:
                images = images.filter(camera_make__name__in=camera_makes)

            if transport_type is not None and transport_type != 'all' and transport_type != '':
                transport_type_obj = TransType.objects.filter(name=transport_type).first()
                if transport_type_obj is not None:
                    children_trans_type = TransType.objects.filter(parent=transport_type_obj)
                    if children_trans_type.count() > 0:
                        types = [transport_type_obj]
                        for t in children_trans_type:
                            types.append(t)
                        sequences = Sequence.objects.filter(transport_type__in=types)
                    else:
                        sequences = Sequence.objects.filter(transport_type=transport_type_obj)

                    images = images.filter(sequence__in=sequences)

            m_type = request.GET.get('type')
            users = None
            if username and username != '':
                users = CustomUser.objects.filter(username__icontains=username)
                if m_type is None or m_type == 'received':
                    images = images.filter(user__in=users)
                elif m_type == 'marked':
                    image_view_points = image_view_points.filter(user__in=users)

            challenge_id = request.GET.get('challenge_id')
            if challenge_id is not None and challenge_id != '':
                label_challenges = label_challenges.filter(unique_id=challenge_id)
                if label_challenges.count() > 0:
                    label_challenge = label_challenges[0]
                    images = images.filter(point__intersects=label_challenge.multipolygon)

            filter_time = request.GET.get('time')
            time_type = request.GET.get('time_type')

            if time_type is None or not time_type or time_type == 'all_time':
                images = images
            else:
                if time_type == 'monthly':
                    if filter_time is None or filter_time == '':
                        now = datetime.now()
                        y = now.year
                        m = now.month
                    else:
                        y = filter_time.split('-')[0]
                        m = filter_time.split('-')[1]
                    images = images.filter(
                        captured_at__month=m,
                        captured_at__year=y
                    )

                elif time_type == 'yearly':
                    if filter_time is None or filter_time == '':
                        now = datetime.now()
                        y = now.year
                    else:
                        y = filter_time
                    images = images.filter(
                        captured_at__year=y
                    )

            if map_feature_value is not None and map_feature_value != '' and map_feature_value != 'all_values':
                print(type(map_feature_value))
                images = images.filter(map_feature_values__contains=tuple([map_feature_value]))

    if images is None:
        images = Image.objects.all()

    images = images.exclude(sequence=None)

    if filter_type == 'label_count':
        # image_json = ImageLabel.objects.filter(
        # image__in=images).values('image').annotate(
        #     image_count=Count('image')).order_by('-image_count').annotate(
        #     rank=Window(expression=RowNumber()))

        tmp_images = images.filter(image_label__isnull=False)

        image_json = tmp_images.values('id').annotate(
            image_count=Count('id')).order_by('-image_count').annotate(
            rank=Window(expression=RowNumber()))


    elif filter_type == 'view_point':
        # image_json = image_view_points.filter(image__in=images).values('image').annotate(image_count=Count('image')).order_by('-image_count').annotate(
        #     rank=Window(expression=RowNumber()))

        images = images.filter(pk__in=image_view_points.values_list('image_id'))
        tmp_images = images
        image_json = images.values('id').annotate(
            image_count=Count('id')).order_by('-image_count').annotate(
            rank=Window(expression=RowNumber()))
    else:
        images = images.order_by('-captured_at')
        tmp_images = images
        image_json = images.values('id').annotate(
            image_count=Count('image_key')).annotate(
            rank=Window(expression=RowNumber()))

    request.session['images_query'] = get_correct_sql(tmp_images)

    paginator = Paginator(image_json, 10)

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
        if 'image' in pItems[i].keys():
            image = images.get(pk=pItems[i]['image'])
        else:
            image = images.get(pk=pItems[i]['id'])

        if image is None or not image:
            continue
        img = {}
        img['unique_id'] = image.unique_id
        img['image_key'] = image.image_key

        try:
            img['image_view_point_count'] = ImageViewPoint.objects.filter(image=image).count()
        except:
            img['image_view_point_count'] = 0

        try:
            img['image_label_count'] = image.image_label.all().count()
        except:
            img['image_label_count'] = 0

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

        try:
            img['map_features'] = ', '.join(image.map_feature_values)
        except:
            img['map_features'] = ''

        pItems[i]['image'] = img


    content = {
        'items': pItems,
        'form': form,
        'pageName': 'Images',
        'pageTitle': 'Images',
        'pageDescription': 'This page shows the photos that have been marked as view points the most number of times.',
        'page': page
    }
    return render(request, 'sequence/image_leaderboard.html', content)


def save_weather(sequence):
    sequence_weathers = SequenceWeather.objects.filter(sequence=sequence)
    if sequence_weathers.count() == 0:
        weatherstack = WeatherStack()

        point = [sequence.get_first_point_lat(), sequence.get_first_point_lng()]
        if isinstance(sequence.captured_at, str):
            historical_date = sequence.captured_at[0:10]
        else:
            historical_date = sequence.captured_at.strftime('%Y-%m-%d')
        weather_json = weatherstack.get_historical_data(point=point, historical_date=historical_date)
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


def get_images_by_multi_sequences(sequences):
    if isinstance(sequences, list) and len(sequences) > 0:
        for sequence in sequences:
            get_images_by_sequence(sequence)


def get_images_by_sequence(sequence, source=None, token=None, image_insert=True, image_download=True, is_weather=True, mf_insert=True):
    seqs = Sequence.objects.filter(unique_id=sequence.unique_id)
    print('sequence importing: ', sequence.seq_key)
    is_print = True
    if seqs.count() == 0:
        print('Sequence is not existing.')
        return
    sequence = seqs[0]
    if is_weather and not sequence.get_first_point_lat() is None and not sequence.get_first_point_lng() is None:
        save_weather(sequence)

    if token is None:
        token = sequence.user.mapillary_access_token
    mapillary = Mapillary(token, source=source)
    image_json = mapillary.get_images_with_ele_by_seq_key([sequence.seq_key])
    if image_json and image_insert:
        image_features = image_json['features']

        if is_print:
            print('Images insert!')

        image_keys = []
        image_position_ary = []
        for image_feature in image_features:
            images = Image.objects.filter(image_key=image_feature['properties']['key'])
            image_position_ary.append(image_feature['geometry']['coordinates'])
            if images.count() > 0:
                image = images[0]
                continue
            else:
                image = Image()
            image_keys.append(image_feature['properties']['key'])


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
            if is_print:
                print('image key: ', image.image_key)

        if len(image_position_ary) > 0 and mf_insert:
            if is_print:
                print('Image len: ', len(image_position_ary))
            mm = 0
            for image_position in image_position_ary:
                i_key = image_features[mm]['properties']['key']
                mm += 1
                if is_print:
                    print('===== {} ====='.format(mm))
                map_feature_json = mapillary.get_map_feature_by_close_to(image_position)
                if map_feature_json:
                    map_features = map_feature_json['features']
                    if is_print:
                        print('map_features len: ', len(map_features))
                    tt = 0
                    for map_feature in map_features:
                        tt += 1
                        mf_properties = map_feature['properties']
                        detections = None
                        if 'detections' in mf_properties.keys():
                            for detection in mf_properties['detections']:
                                image_key = detection['image_key']
                                if image_key == i_key:
                                    detections = detection
                                    break
                        if detections is None:
                            continue
                        mf_geometry = map_feature['geometry']
                        mf_item = MapFeature.objects.filter(mf_key=mf_properties['key'])[:1]
                        if mf_item.count() > 0:
                            continue
                        mf_item = MapFeature()
                        mf_item.detections = {'detections': detections}
                        if 'accuracy' in mf_properties.keys():
                            mf_item.accuracy = mf_properties['accuracy']
                        if 'altitude' in mf_properties.keys():
                            mf_item.altitude = mf_properties['altitude']
                        if 'direction' in mf_properties.keys():
                            mf_item.direction = mf_properties['direction']
                        if 'first_seen_at' in mf_properties.keys():
                            mf_item.first_seen_at = mf_properties['first_seen_at']
                        if 'key' in mf_properties.keys():
                            mf_item.mf_key = mf_properties['key']
                        if 'last_seen_at' in mf_properties.keys():
                            mf_item.last_seen_at = mf_properties['last_seen_at']
                        if 'layer' in mf_properties.keys():
                            mf_item.layer = mf_properties['layer']
                        if 'value' in mf_properties.keys():
                            mf_item.value = mf_properties['value']
                        mf_item.geometry_type = mf_geometry['type']
                        mf_item.geometry_point = Point(mf_geometry['coordinates'])
                        mf_detection_keys = []
                        mf_image_keys = []
                        mf_user_keys = []
                        for detection in mf_properties['detections']:
                            mf_detection_keys.append(detection['detection_key'])
                            mf_image_keys.append(detection['image_key'])
                            mf_user_keys.append(detection['user_key'])
                        mf_item.detection_keys = mf_detection_keys
                        mf_item.image_keys = mf_image_keys
                        mf_item.user_keys = mf_user_keys
                        mf_item.save()

                        image = Image.objects.filter(image_key=i_key).first()
                        if image is not None:
                            mf_keys = image.map_feature_keys
                            if mf_keys is None:
                                mf_keys = []
                            if mf_item.mf_key not in mf_keys:
                                mf_keys.append(mf_item.mf_key)
                            image.map_feature_keys = mf_keys

                            mf_values = image.map_feature_values
                            if mf_values is None:
                                mf_values = []
                            if mf_item.value not in mf_values:
                                mf_values.append(mf_item.value)
                            image.map_feature_values = mf_values

                            image.save()

                        # for detection in mf_properties['detections']:
                        #     detection_key = detection['detection_key']
                        #     image_key = detection['image_key']
                        #     user_key = detection['user_key']
                        #     mf_key = mf_item.mf_key
                        #     print(detection)
                        #     mf_detection = MapFeatureDetection.objects.filter(map_feature=mf_item, detection_key=detection_key,
                        #                                                       image_key=image_key, user_key=user_key)
                        #     if mf_detection.count() > 0:
                        #         continue
                        #     else:
                        #         mf_detection = MapFeatureDetection()
                        #         mf_detection.map_feature = mf_item
                        #         mf_detection.detection_key = detection_key
                        #         mf_detection.image_key = image_key
                        #         mf_detection.user_key = user_key
                        #         mf_detection.save()
            sequence.is_map_feature = True
            sequence.save()


        if not settings.DEBUG and len(image_keys) > 0 and image_download:
            if is_print:
                print('image_download')
            # Create the model you want to save the image to
            for image_key in image_keys:
                images = Image.objects.filter(image_key=image_key)
                if images.count() == 0:
                    if is_print:
                        print('image_count: ', images.count())
                    continue
                if not images[0].mapillary_image is None and images[0].mapillary_image != '':
                    if is_print:
                        print(images[0].mapillary_image)
                        print('mapillary_image is not none')
                    continue
                image = images[0]

                lf = mapillary.download_mapillary_image(image.image_key)
                # Save the temporary image to the model#
                # This saves the model so be sure that is it valid
                if lf:
                    print('image: ', image.image_key)
                    image.mapillary_image.save(image.image_key, files.File(lf))
                    image.save()
            sequence.is_image_download = True
            sequence.save()


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
    # if not sequence.is_published and request.user != sequence.user:
    #     messages.error(request, 'The sequence is not published.')
    #     return redirect('sequence.index')
    # print('1')
    # p = threading.Thread(target=get_images_by_sequence, args=(sequence,))
    # p.start()
    # print('2')
    # set_camera_make(sequence)

    image_key = None



    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        image_key = request.GET.get('image_key')
        if page is None:
            page = 1

        view_mode = request.GET.get('view_mode')
        if view_mode is None:
            view_mode = 'original'

        show_gpx = request.GET.get('show_gpx')
        if show_gpx is None:
            show_gpx = 'false'

        show_street_level_poi = request.GET.get('show_street_level_poi')
        if show_street_level_poi is None:
            show_street_level_poi = 'false'

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
    is_marked_point = False
    imgs = Image.objects.filter(image_key=coordinates_image[0])
    if imgs.count() > 0:
        i_vs = ImageViewPoint.objects.filter(image=imgs[0])
        view_points = i_vs.count()
        if view_points > 0:
            if i_vs.filter(user=request.user).first() is not None:
                is_marked_point = True
    addSequenceForm = AddSequenceForm(instance=sequence)

    label_types = LabelType.objects.filter(parent__isnull=False)
    tours = TourSequence.objects.filter(sequence=sequence)
    tour_count = tours.count()
    sequence_weathers = SequenceWeather.objects.filter(sequence=sequence)
    sequence_weather = None
    if sequence_weathers.count() > 0:
        sequence_weather = sequence_weathers[0]

    if image_key is not None and image_key != '':
        firstImageKey = image_key
    else:
        firstImageKey = sequence.get_first_image_key()

    guidebooks = None
    if request.user.is_authenticated:
        guidebooks = Guidebook.objects.filter(user=request.user)
        if guidebooks.count() == 0:
            guidebooks = None

    is_mine = False
    tours = None
    ts_tours = None
    if request.user.is_authenticated and request.user == sequence.user:
        is_mine = True
        tours = Tour.objects.filter(user=request.user)
        tour_sequences = TourSequence.objects.filter(sequence=sequence)
        ts_tours = None
        for tour_sequence in tour_sequences:
            if ts_tours is None:
                ts_tours = []
            ts_tours.append(tour_sequence.tour)

    content = {
        'sequence': sequence,
        'guidebooks': guidebooks,
        'pageName': 'Sequence Detail',
        'pageTitle': sequence.name + ' - Sequence',
        'pageDescription': sequence.description,
        'first_image': images[0],
        'page': page,
        'view_points': view_points,
        'is_marked_point': is_marked_point,
        'addSequenceForm': addSequenceForm,
        'label_types': label_types,
        'image_key': image_key,
        'tour_count': tour_count,
        'sequence_weather': sequence_weather,
        'view_mode': view_mode,
        'show_gpx': show_gpx,
        'show_street_level_poi': show_street_level_poi,
        'firstImageKey': firstImageKey,
        'tours': tours,
        'ts_tours': ts_tours,
        'is_mine': is_mine
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
        sequence.delete()

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
        form = AddSequenceForm(request.POST)

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
                    if tag not in form.cleaned_data['tag']:
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

        if month is not None:
            search_form.set_month(month)

            y = month.split('-')[0]
            m = month.split('-')[1]

            map_users = MapillaryUser.objects.filter(user=request.user)
            if map_users.count() == 0:
                return redirect('home')
            else:
                map_user = map_users[0]

            features = []
            sequences_ary = []

            # if page is none, then call mapillary api.
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
                # features.sort(key=sort_by_captured_at)
                request.session['sequences'] = features

                page = 1

                for seq in features:
                    seq_s = Sequence.objects.filter(seq_key=seq['properties']['key'])[:1]
                    if seq_s.count() == 0:
                        sequences_ary.append(seq)
                request.session['sequences'] = sequences_ary

            else:
                sequences_ary = request.session['sequences']

            paginator = Paginator(sequences_ary, 10)
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
                    sequences[i]['tags'] = seq[0].get_tags()
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
                if sequences[i]['image_count'] > 0:
                    sequences[i]['first_image_key'] = sequences[i]['properties']['coordinateProperties']['image_keys'][0]
                else:
                    sequences[i]['first_image_key'] = ''


    addSequenceForm = AddSequenceForm()

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

        # form = AddSequenceForm(request.POST)
        # if form.is_valid():
        # for unique_id in sequence_json.keys():
        #     sequence = Sequence.objects.get(unique_id=unique_id)
        #     if sequence is None:
        #         continue
        #     if sequence_json[unique_id]['name'] == '' or sequence_json[unique_id]['description'] == '' or sequence_json[unique_id]['transport_type'] == 0 or len(sequence_json[unique_id]['tags']) == 0:
        #         continue
        form = AddSequenceForm(request.POST)
        if form.is_valid():

            # for i in range(len(request.session['sequences'])):
            seq_index = 0
            sequences = []
            sequence_unique_id = ""
            for feature in request.session['sequences']:
                # feature = request.session['sequences'][i]
                if feature['properties']['key'] == seq_key:
                    properties = feature['properties']
                    geometry = feature['geometry']
                    sequence = Sequence.objects.filter(seq_key=seq_key).first()

                    if sequence is not None:
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
                        sequence.is_private = properties['private']

                    # if name empty, then use captured_at
                    if form.cleaned_data['name'] is None or form.cleaned_data['name'] == '':
                        captured_at = datetime.strptime(sequence.captured_at, '%Y-%m-%dT%H:%M:%S.000%z')
                        sequence.name = captured_at.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        sequence.name = form.cleaned_data['name']
                    sequence.description = form.cleaned_data['description']
                    sequence.transport_type = form.cleaned_data['transport_type']
                    sequence.is_published = False
                    sequence.save()

                    sequence.distance = sequence.get_distance()
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

                    sequence_unique_id = str(sequence.unique_id)
                    continue

                sequences.append(feature)

            request.session['sequences'] = sequences

            return JsonResponse({
                'status': 'success',
                'message': 'Sequence successfully imported. Sequence will be published in about 30 minutes.',
                'unique_id': sequence_unique_id
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


@my_login_required
def ajax_multi_import(request):
    if request.method == 'POST':
        sequence_keys_str = request.POST.get('sequence_keys')
        transport_type = request.POST.get('transport_type')

        if sequence_keys_str is not None and sequence_keys_str != '' and transport_type is not None and transport_type != '':
            sequence_keys = sequence_keys_str.split(',')
            sequences = []
            sequence_unique_id = ""
            for feature in request.session['sequences']:
                # feature = request.session['sequences'][i]
                if feature['properties']['key'] in sequence_keys:
                    properties = feature['properties']
                    geometry = feature['geometry']
                    sequence = Sequence.objects.filter(seq_key=feature['properties']['key'])[:1]

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
                        sequence.is_private = properties['private']

                    sequence.name = str(properties['captured_at'])
                    sequence.description = None
                    sequence.transport_type = transport_type
                    sequence.is_published = True
                    sequence.save()

                    sequence.distance = sequence.get_distance()
                    sequence.save()

                    set_camera_make(sequence)

                    continue

                sequences.append(feature)

            request.session['sequences'] = sequences

            if len(sequences) > 0:
                # get image data from mapillary with sequence_key
                print('1')
                p = threading.Thread(target=get_images_by_multi_sequences, args=(sequences,))
                p.start()
                print('2')
                # messages.success(request, "Sequences successfully imported.")

            return JsonResponse({
                'status': 'success',
                'message': 'Sequences successfully imported. Sequences will be published in about 30 minutes or longer.'
            })
        else:
            errors = []

            return JsonResponse({
                'status': 'failed',
                'message': 'Error'
            })
    return JsonResponse({
        'status': 'failed',
        'message': 'Sequences were not imported.'
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

    sequence_like = SequenceLike.objects.filter(sequence=sequence, user=request.user)
    if sequence_like:
        if sequence.user.is_liked_email:
            # confirm email
            try:
                # send email to creator
                subject = 'Your Map the Paths Sequence Was Liked'
                html_message = render_to_string(
                    'emails/sequence/like.html',
                    {'subject': subject, 'like': 'unliked', 'sequence': sequence, 'sender': request.user},
                    request
                )
                send_mail_with_html(subject, html_message, sequence.user.email, settings.SMTP_REPLY_TO)
            except:
                print('email sending error!')
        for g in sequence_like:
            g.delete()
        liked_sequence = SequenceLike.objects.filter(sequence=sequence)
        if not liked_sequence:
            liked_count = 0
        else:
            liked_count = liked_sequence.count()
        sequence.like_count = liked_count
        sequence.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Unliked',
            'is_checked': False,
            'liked_count': liked_count
        })
    else:
        if sequence.user.is_liked_email:
            # confirm email
            try:
                # send email to creator
                subject = 'Your Map the Paths Sequence Was Liked'
                html_message = render_to_string(
                    'emails/sequence/like.html',
                    {'subject': subject, 'like': 'liked', 'sequence': sequence, 'sender': request.user},
                    request
                )
                send_mail_with_html(subject, html_message, sequence.user.email, settings.SMTP_REPLY_TO)
            except:
                print('email sending error!')
        sequence_like = SequenceLike()
        sequence_like.sequence = sequence
        sequence_like.user = request.user
        sequence_like.save()
        liked_sequence = SequenceLike.objects.filter(sequence=sequence)
        if not liked_sequence:
            liked_count = 0
        else:
            liked_count = liked_sequence.count()
        sequence.like_count = liked_count
        sequence.save()
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

    images = Image.objects.filter(image_key=image_key, sequence=sequence)[:1]
    if images.count() > 0:
        image = images[0]
    else:
        return JsonResponse({
            'status': 'failed',
            'message': "Image outside of current sequence",
        })

    view_points = ImageViewPoint.objects.filter(image=image)
    is_marked_point = False
    if view_points.count() > 0:
        if view_points.filter(user=request.user).first() is not None:
            is_marked_point = True
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
        'view_points': view_points.count(),
        'is_marked_point': is_marked_point
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
            if image_label.point is not None:
                geometry = image_label.point.coords
                geo_type = 'point'
            elif image_label.polygon is not None:
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
    if request.method == 'POST':
        label_type_keys = request.POST.get('keys')
        if label_type_keys is not None and label_type_keys != '':
            label_types = label_type_keys.split(',')
            if len(label_types) > 0:
                for label_type in label_types:
                    l_ary = label_type.split('--')
                    ind = 0
                    if len(l_ary) > 0:
                        l_type = None
                        for lab in l_ary:
                            if ind == 0:
                                types = LabelType.objects.filter(parent__isnull=True, name=lab)
                            else:
                                types = LabelType.objects.filter(parent=l_type, name=lab)
                            if types.count() == 0:
                                l_parent_type = l_type
                                l_type = LabelType()
                                l_type.name = lab
                                l_type.source = 'mapillary'
                                l_type.parent = l_parent_type
                                l_type.save()
                            else:
                                l_type = types[0]
                            ind += 1

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
        label_types = LabelType.objects.filter(pk=label_id)[:1]
        if label_types.count() == 0:
            return JsonResponse({
                'status': 'failed',
                'message': 'The label type does not exist.'
            })
        else:
            label_type = label_types[0]
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
    sequence = Sequence.objects.filter(unique_id=unique_id).first()
    if sequence is None:
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
    if image_key is not None and len(images) > 0:
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
            if image[0].map_feature_values is None:
                pImages[i]['map_features'] = ''
            else:
                pImages[i]['map_features'] = ','.join(image[0].map_feature_values)

    addSequenceForm = AddSequenceForm(instance=sequence)

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

    if not sequence.is_published:
        return JsonResponse({
            'status': 'failed',
            'message': "This sequence is not published."
        })

    image = Image.objects.filter(seq_key=sequence.seq_key, image_key=image_key).first()

    if image is None:
        return JsonResponse({
            'status': 'failed',
            'message': "The Image does not exist."
        })


    image_view_points = ImageViewPoint.objects.filter(image=image, user=request.user)
    if image_view_points.count() > 0:
        if sequence.user.is_liked_email:
            # confirm email
            try:
                # send email to creator
                subject = 'Your Map the Paths Photo Received a View Point'
                html_message = render_to_string(
                    'emails/sequence/image_view_point.html',
                    {'subject': subject, 'like': 'unviewed', 'sequence': sequence, 'image_key': image.image_key, 'sender': request.user},
                    request
                )
                email_thread = threading.Thread(target=send_mail_with_html, args=(subject, html_message, sequence.user.email, settings.SMTP_REPLY_TO,))
                email_thread.start()
                # send_mail_with_html(subject, html_message, sequence.user.email, settings.SMTP_REPLY_TO)
            except:
                print('email sending error!')
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
        if sequence.user.is_liked_email:
            # confirm email
            try:
                # send email to creator
                subject = 'Your Map the Paths Photo Received a View Point'
                html_message = render_to_string(
                    'emails/sequence/image_view_point.html',
                    {'subject': subject, 'like': 'viewed', 'sequence': sequence, 'image_key': image.image_key, 'sender': request.user},
                    request
                )
                email_thread = threading.Thread(target=send_mail_with_html, args=(subject, html_message, sequence.user.email, settings.SMTP_REPLY_TO,))
                email_thread.start()
                # send_mail_with_html(subject, html_message, sequence.user.email, settings.SMTP_REPLY_TO)
            except:
                print('email sending error!')
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


def ajax_image_map_feature(request, unique_id):
    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    image_key = request.GET.get('image_key', '')
    map_features_json = {}
    features = []
    if image_key is not None and image_key != '':
        map_features = MapFeature.objects.filter(image_keys__contains=[image_key])
        for map_feature in map_features:
            value = map_feature.value
            if value in map_features_json.keys():
                map_features_json[value] += 1
            else:
                map_features_json[value] = 1
            features.append({
                'value': map_feature.value,
                'mf_key': map_feature.mf_key,
                'geometry_type': map_feature.geometry_type,
                'lon': map_feature.geometry_point.coords[0],
                'lat': map_feature.geometry_point.coords[1],
                'accuracy': map_feature.accuracy,
                'altitude': map_feature.altitude,
                'direction': map_feature.direction,
                'layer': map_feature.layer,
            })
    data = {
        'map_features': map_features_json,
        'features': features
    }

    return JsonResponse(data)


def ajax_get_image_gpx_data(request, unique_id):
    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    images = Image.objects.filter(sequence=sequence)
    points = []
    for image in images:
        points.append({
            'lat': image.point.coords[1],
            'lon': image.point.coords[0],
            'ele': image.ele,
            'time': image.captured_at
        })

    return JsonResponse({'points': points})


def ajax_add_in_tour(request, unique_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': 'You are required login.'
        })

    sequence = Sequence.objects.filter(unique_id=unique_id, user=request.user).first()

    if sequence is None or not sequence.is_published:
        return JsonResponse({
            'status': 'failed',
            'message': "The Sequence does not exist or you don't have access."
        })

    if request.method == 'POST':
        tour_sequences = TourSequence.objects.filter(sequence=sequence).order_by('sort')

        tour_ids = request.POST.get('tour_ids')
        tour_id_ary = tour_ids.split(',')
        max_sort = 0

        for tour_sequence in tour_sequences:

            unique_id_str = str(tour_sequence.tour.unique_id)
            if unique_id_str not in tour_id_ary:
                tour = tour_sequence.tour
                tour_sequence.delete()
                ts = TourSequence.objects.filter(tour=tour)
                if ts.count() == 0:
                    tour.is_published = False
                    tour.save()
            else:
                tour_id_ary.remove(unique_id_str)
                max_sort = tour_sequence.sort

        for tour_id in tour_id_ary:
            if tour_id == '':
                continue
            tour = Tour.objects.get(unique_id=tour_id)
            if tour is not None:
                tour_sequence = TourSequence()
                tour_sequence.tour = tour
                tour_sequence.sequence = sequence
                max_sort += 1
                tour_sequence.sort = max_sort
                tour_sequence.save()

                tour.is_published = True
                tour.save()

    return JsonResponse({
            'status': 'success',
            'message': "Sequence is successfully updated in tours."
        })


def ajax_get_detail_by_image_key(request, image_key):
    images = Image.objects.filter(image_key=image_key)
    if images.count() == 0:
        return JsonResponse({
            'status': 'failed',
            'message': "Image key error."
        })
    image = images[0]
    sequence = image.sequence
    if request.user == sequence.user:
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
        data['sequence_unique_id'] = sequence.unique_id

    return JsonResponse(data)


def ajax_get_map_features(request):
    map_feature_json = MapFeature.objects.all().values('value').annotate(
        image_count=Count('value')).order_by('-image_count').annotate(
        rank=Window(expression=RowNumber()))

    map_feature_values = []
    for map_feature in map_feature_json:
        map_feature_values.append(map_feature['value'])

    return JsonResponse({
        'status': 'success',
        'map_features': map_feature_values
    })


def ajax_get_import_sequences(request):
    if request.session['sequences'] is not None:
        print('sequence len: ', len(request.session['sequences']))
        return JsonResponse({
            'status': 'success',
            'sequences': request.session['sequences'],
            'message': 'success'
        })
    else:
        return JsonResponse({
            'status': 'failed',
            'sequences': None,
        })


def ajax_get_import_sequence(request):
    sequence_key = request.GET.get('sequence_key')
    if sequence_key is not None:
        pass
    if request.session['sequences'] is not None:
        return JsonResponse({
            'status': 'success',
            'sequences': request.session['sequences'],
            'message': 'success'
        })
    else:
        return JsonResponse({
            'status': 'failed',
            'sequences': None,
        })


def ajax_get_import_next_sequence_id(request):
    sequence_key = request.GET.get('sequence_key')
    print(sequence_key)
    is_seq = False
    next_sequence_key = ''
    for feature in request.session['sequences']:
        # feature = request.session['sequences'][i]
        if feature['properties']['key'] == sequence_key:
            is_seq = True
            continue
        if is_seq:
            next_sequence_key = feature['properties']['key']
            break
    print('next_sequence_key', next_sequence_key)
    return JsonResponse({
        'status': 'success',
        'next_sequence_key': next_sequence_key,
        'message': 'success'
    })


def ajax_check_import_limit(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't change the status."
        })
    user = request.user

    user_grade = user.user_grade
    sequence_limit_count = 5
    if user_grade is not None:
        sequence_limit_count = user_grade.sequence_limit_count

    from datetime import timedelta, time
    today = datetime.now().date()
    tomorrow = today + timedelta(1)
    today_start = datetime.combine(today, time())
    today_end = datetime.combine(tomorrow, time())

    today_imported_sequences = Sequence.objects.filter(user=user, is_mapillary=True, imported_at__gte=today_start, imported_at__lt=today_end)

    today_count = len(today_imported_sequences)

    return JsonResponse({
        'status': 'success',
        'sequence_limit_count': sequence_limit_count - today_count
    })


def manual_update(request):

    # for map_feature in map_features:
    #     image_keys = map_feature.image_keys
    #     for image_key in image_keys:
    #         images = Image.objects.filter(image_key=image_key)
    #         for image in images:
    #             print('sequence id: {}, image key: {}'.format(image.sequence.unique_id, image.image_key))

    # p = threading.Thread(target=update_mf_keys_with_thread)
    # p.start()
    #
    # p = threading.Thread(target=change_map_feature_field)
    # p.start()
    method = request.GET.get('method')
    if method == 'sort_by_like':
        sequences = Sequence.objects.all()
        for sequence in sequences:
            sequence.like_count = sequence.get_like_count()
            sequence.save()
        guidebooks = Guidebook.objects.all()
        for guidebook in guidebooks:
            guidebook.like_count = guidebook.get_like_count()
            guidebook.save()
        tours = Tour.objects.all()
        for tour in tours:
            tour.like_count = tour.get_like_count()
            tour.save()


    if method == 'google_street_view':
        sequences = Sequence.objects.all()
        for sequence in sequences:
            if sequence.google_street_view == False or sequence.google_street_view == 'false':
                sequence.google_street_view = ''
                sequence.save()

    return redirect('home')


def update_mf_keys_with_thread():
    images = Image.objects.all()
    print('len image: ', images.count())
    m = 0
    for image in images:
        m += 1
        print('number image: ', m)
        mf_values = None
        mf_keys = image.map_feature_keys
        if mf_keys is not None:
            for mf_key in mf_keys:
                mf = MapFeature.objects.filter(mf_key=mf_key).first()
                if mf is not None:
                    mf_value = mf.value
                    if mf_values is None:
                        mf_values = []
                    if mf_value not in mf_values:
                        mf_values.append(mf_value)
        if mf_values is not None:
            image.map_feature_values = mf_values

            print(mf_values)
            image.save()


def insert_db_with_thread():
    sequences = Sequence.objects.all()
    for sequence in sequences:
        get_images_by_sequence(sequence=sequence, mf_insert=True, image_download=False)


def change_download_field():
    sequences = Sequence.objects.all()
    for sequence in sequences:
        sequence.is_image_download = True
        sequence.save()


def change_map_feature_field():
    sequences = Sequence.objects.all()
    for sequence in sequences:
        sequence.is_map_feature = True
        sequence.save()
