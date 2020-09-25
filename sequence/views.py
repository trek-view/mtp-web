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
            camera_make = form.cleaned_data['camera_make']
            tags = form.cleaned_data['tag']
            transport_type = form.cleaned_data['transport_type']
            username = form.cleaned_data['username']
            like = form.cleaned_data['like']

            sequences = Sequence.objects.all().filter(
                is_published=True
            ).exclude(image_count=0)
            if name and name != '':
                sequences = sequences.filter(name__contains=name)
            if camera_make and camera_make != '':
                sequences = sequences.filter(camera_make__contains=camera_make)
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
            camera_make = form.cleaned_data['camera_make']
            tags = form.cleaned_data['tag']
            transport_type = form.cleaned_data['transport_type']
            like = form.cleaned_data['like']

            sequences = Sequence.objects.all().filter(
                user=request.user
            ).exclude(image_count=0)
            if name and name != '':
                sequences = sequences.filter(name__contains=name)
            if camera_make and camera_make != '':
                sequences = sequences.filter(camera_make__contains=camera_make)
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

def get_images_by_sequence(sequence, source=None, token=None, image_insert=True, detection_insert=False, mf_insert=True, image_download=True):
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
            if 'camera_make' in image_feature['properties'].keys():
                image.camera_make = image_feature['properties']['camera_make']
            if 'camera_model' in image_feature['properties'].keys():
                image.camera_model = image_feature['properties']['camera_model']
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

        # if len(image_keys) > 0 and image_download:
        #     # Create the model you want to save the image to
        #     for image_key in image_keys:
        #         images = Image.objects.filter(image_key=image_key)
        #         if images.count() == 0:
        #             continue
        #         if not images[0].mapillary_image is None:
        #             continue
        #         image = images[0]
        #
        #         lf = mapillary.download_mapillary_image(image.image_key)
        #         # Save the temporary image to the model#
        #         # This saves the model so be sure that is it valid
        #         if lf:
        #             image.mapillary_image.save(image.image_key, files.File(lf))
        #             image.save()
        #             print(image.mapillary_image)
        #
        # if len(image_keys) > 0 and detection_insert:
        #     detection_types = ['trafficsigns', 'segmentations', 'instances']
        #     for detection_type in detection_types:
        #         image_keys_t = []
        #         image_num = 0
        #         for image_k in image_keys:
        #             image_keys_t.append(image_k)
        #             image_num += 1
        #             if (len(image_keys_t) == 10 or image_num == len(image_keys)) and len(image_keys_t) > 0:
        #                 print(image_keys_t)
        #                 image_detection_json = mapillary.get_detection_by_image_key(image_keys_t, detection_type)
        #                 if image_detection_json:
        #                     image_detection_features = image_detection_json['features']
        #                     for image_detection_feature in image_detection_features:
        #                         properties = image_detection_feature['properties']
        #                         geometry = image_detection_feature['geometry']
        #                         image_detection = ImageDetection.objects.filter(image_key=properties['key'])
        #                         if image_detection.count() > 0:
        #                             continue
        #                         image_detection = ImageDetection()
        #                         images = Image.objects.filter(image_key=properties['image_key'])[:1]
        #                         if images.count() == 0:
        #                             continue
        #
        #                         if 'area' in properties.keys():
        #                             image_detection.area = properties['area']
        #                         if 'captured_at' in properties.keys():
        #                             image_detection.captured_at = properties['captured_at']
        #                         if 'image_ca' in properties.keys():
        #                             image_detection.image_ca = properties['image_ca']
        #                         if 'image_key' in properties.keys():
        #                             image_detection.image_key = properties['image_key']
        #                         if 'image_pano' in properties.keys():
        #                             image_detection.image_pano = properties['image_pano']
        #                         if 'key' in properties.keys():
        #                             image_detection.det_key = properties['key']
        #                         if 'score' in properties.keys():
        #                             image_detection.score = properties['score']
        #                         if 'shape' in properties.keys():
        #                             image_detection.shape_type = properties['shape']['type']
        #                         if 'shape' in properties.keys():
        #                             coordinates = properties['shape']['coordinates']
        #                             multiPolygon = MultiPolygon()
        #                             for coordinate in coordinates:
        #                                 polygon = Polygon(coordinate)
        #                                 multiPolygon.append(polygon)
        #                             image_detection.shape_multipolygon = multiPolygon
        #                         if 'value' in properties.keys():
        #                             image_detection.value = properties['value']
        #
        #                         image_detection.geometry_type = geometry['type']
        #                         image_detection.geometry_point = Point(geometry['coordinates'])
        #                         image_detection.type = detection_type
        #                         image_detection.save()
        #                         print('image detection: ', image_detection.det_key)
        #                 image_keys_t = []
        #                 continue
        #
        # if len(image_position_ary) > 0 and mf_insert:
        #     print('Image len: ', len(image_position_ary))
        #     mm = 0
        #     for image_position in image_position_ary:
        #         mm += 1
        #         print('===== {} ====='.format(mm))
        #         map_feature_json = mapillary.get_map_feature_by_close_to(image_position)
        #         if map_feature_json:
        #             map_features = map_feature_json['features']
        #             print('map_features len: ', len(map_features))
        #             tt = 0
        #             for map_feature in map_features:
        #                 tt += 1
        #                 print('---- {} -----'.format(tt))
        #                 mf_properties = map_feature['properties']
        #                 mf_geometry = map_feature['geometry']
        #                 mf_item = MapFeature.objects.filter(mf_key=mf_properties['key'])[:1]
        #                 if mf_item.count() > 0:
        #                     continue
        #
        #                 mf_item = MapFeature()
        #                 if 'accuracy' in mf_properties.keys():
        #                     mf_item.accuracy = mf_properties['accuracy']
        #                 if 'altitude' in mf_properties.keys():
        #                     mf_item.altitude = mf_properties['altitude']
        #                 if 'direction' in mf_properties.keys():
        #                     mf_item.direction = mf_properties['direction']
        #                 if 'first_seen_at' in mf_properties.keys():
        #                     mf_item.first_seen_at = mf_properties['first_seen_at']
        #                 if 'key' in mf_properties.keys():
        #                     mf_item.mf_key = mf_properties['key']
        #                 if 'last_seen_at' in mf_properties.keys():
        #                     mf_item.last_seen_at = mf_properties['last_seen_at']
        #                 if 'layer' in mf_properties.keys():
        #                     mf_item.layer = mf_properties['layer']
        #                 if 'value' in mf_properties.keys():
        #                     mf_item.value = mf_properties['value']
        #
        #                 mf_item.geometry_type = mf_geometry['type']
        #                 mf_item.geometry_point = Point(mf_geometry['coordinates'])
        #
        #                 mf_item.save()
        #
        #                 if 'detections' in mf_properties.keys():
        #                     for detection in mf_properties['detections']:
        #                         detection_key = detection['detection_key']
        #                         image_key = detection['image_key']
        #                         user_key = detection['user_key']
        #                         mf_key = mf_item.mf_key
        #                         print(detection)
        #                         mf_detection = MapFeatureDetection.objects.filter(mf_key=mf_key, detection_key=detection_key, image_key=image_key, user_key=user_key)
        #                         if mf_detection.count() > 0:
        #                             continue
        #                         else:
        #                             mf_detection = MapFeatureDetection()
        #                             mf_detection.mf_key = mf_key
        #                             mf_detection.detection_key = detection_key
        #                             mf_detection.image_key = image_key
        #                             mf_detection.user_key = user_key
        #                             mf_detection.save()

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

    set_camera_make(sequence)
    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1

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

    label_types = LabelType.objects.all()

    content = {
        'sequence': sequence,
        'pageName': 'Sequence Detail',
        'pageTitle': sequence.name + ' - Sequence',
        'pageDescription': sequence.description,
        'first_image': images[0],
        'page': page,
        'view_points': view_points,
        'addSequenceForm': addSequenceForm,
        'label_types': label_types
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

            map_user = MapillaryUser.objects.get(user=request.user)
            if map_user is None:
                return redirect('home')

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
                    if 'camera_make' in properties:
                        sequence.camera_make = properties['camera_make']
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

                    lineString = LineString()
                    firstPoint = None
                    if sequence.image_count == 0:
                        firstPoint = Point(sequence.geometry_coordinates_ary[0][0], sequence.geometry_coordinates_ary[0][1])
                        lineString = LineString(firstPoint.coords, firstPoint.coords)
                    else:
                        for i in range(len(sequence.geometry_coordinates_ary)):
                            coor = sequence.geometry_coordinates_ary[i]
                            if i == 0:
                                firstPoint = Point(coor[0], coor[1])
                                continue
                            point = Point(coor[0], coor[1])
                            if i == 1:
                                lineString = LineString(firstPoint.coords, point.coords)
                            else:
                                lineString.append(point.coords)

                    sequence.geometry_coordinates = lineString

                    sequence.coordinates_cas = properties['coordinateProperties']['cas']
                    sequence.coordinates_image = properties['coordinateProperties']['image_keys']
                    if 'private' in properties:
                        sequence.is_privated = properties['private']

                    sequence.name = form.cleaned_data['name']
                    sequence.description = form.cleaned_data['description']
                    sequence.transport_type = form.cleaned_data['transport_type']
                    sequence.is_published = True
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
        'guidebook_count': scenes.count()
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
            'message': 'A new label is successfully added.'
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

    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        print('page', page)
        if page is None:
            page = 1

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
        'addSequenceForm': addSequenceForm
    }

    image_list_box_html = render_to_string(
        'sequence/image_list_box.html',
        content,
        request
    )

    return JsonResponse({
        'image_list_box_html': image_list_box_html,
        'page': page,
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
