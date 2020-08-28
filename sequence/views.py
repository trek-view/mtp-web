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
from django.contrib.gis.geos import Point, LineString

## Custom Libs ##
from lib.functions import *

## Project packages
from accounts.models import CustomUser, MapillaryUser
from tour.models import Tour, TourSequence

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
    if request.user.mapillary_access_token == '' or request.user.mapillary_access_token is None:
        return redirect(settings.MAPILLARY_AUTHENTICATION_URL)
    else:
        map_user = get_mapillary_user(request.user.mapillary_access_token)
        if map_user is None:
            return redirect(settings.MAPILLARY_AUTHENTICATION_URL)
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
            # start_time = form.cleaned_data['start_time']
            # end_time = form.cleaned_data['end_time']
            username = form.cleaned_data['username']

            sequences = Sequence.objects.all().filter(
                is_published=True,
                is_transport=True
            )
            if name and name != '':
                sequences = sequences.filter(name__contains=name)
            if camera_make and camera_make != '':
                sequences = sequences.filter(camera_make__contains=camera_make)
            if transport_type and transport_type != 0 and transport_type != '':
                sequences = sequences.filter(transport_type_id=transport_type)
            if username and username != '':
                sequences = sequences.filter(username__contains=username)
            if len(tags) > 0:
                sequences = sequences.filter(tag__overlap=tags)

    print(sequences)
    if sequences == None:
        sequences = Sequence.objects.all().filter(is_published=True, is_approved=True)
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
    print(pSequences.count)
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
            # start_time = form.cleaned_data['start_time']
            # end_time = form.cleaned_data['end_time']
            username = form.cleaned_data['username']

            sequences = Sequence.objects.all().filter(
                user=request.user,
                is_transport=True
            )
            if name and name != '':
                sequences = sequences.filter(name__contains=name)
            if camera_make and camera_make != '':
                sequences = sequences.filter(camera_make__contains=camera_make)
            if transport_type and transport_type != 0 and transport_type != '':
                sequences = sequences.filter(category_id=transport_type)
            if username and username != '':
                sequences = sequences.filter(username__contains=username)
            if len(tags) > 0:
                sequences = sequences.filter(tag__overlap=tags)

    print(sequences)
    if sequences == None:
        sequences = Sequence.objects.all().filter(is_published=True, is_approved=True)
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
    print(pSequences.count)
    content = {
        'sequences': pSequences,
        'form': form,
        'pageName': 'My Sequences',
        'pageTitle': 'Sequences',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page
    }
    return render(request, 'sequence/list.html', content)

def sequence_detail(request, unique_id):
    sequence = get_object_or_404(Sequence, unique_id=unique_id)
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

    addSequenceForm = AddSequeceForm(instance=sequence)
    content = {
        'sequence': sequence,
        'images': pImages,
        'origin_images': origin_images,
        'pageName': 'Sequence Detail',
        'pageTitle': 'Sequence',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page,
        'first_image': pImages[0],
        'addSequenceForm': addSequenceForm
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
        sequence.tag = None
        sequence.is_published = False
        sequence.is_transport = False
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
            sequence.tag = form.cleaned_data['tag']
            sequence.save()

            tags = []
            if len(sequence.tag) > 0:
                for t in sequence.tag:
                    tag = Tag.objects.get(pk=t)
                    if not tag or tag is None:
                        continue
                    tags.append(tag.name)

            return JsonResponse({
                'status': 'success',
                'message': 'This sequence is updated successfully.',
                'sequence': {
                    'name': sequence.name,
                    'description': sequence.description,
                    'transport_type': sequence.transport_type.name,
                    'tags': tags
                }
            })

    return JsonResponse({
        'status': 'failed',
        'message': 'The sequence does not exist or has no access.'
    })

def ajax_get_image_detail(request, unique_id, image_key):
    pass
    return

@my_login_required
def import_sequence_list(request):
    sequences = []
    search_form = TransportSearchForm()
    page = 1
    action = 'filter'
    if request.method == "GET":
        month = request.GET.get('month')
        page = request.GET.get('page')
        if page is None:
            page = 1
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

            if action == 'filter':
                end_seq = Sequence.objects.filter(
                    user=request.user,
                    user_key=map_user.key,
                    captured_at__year=y,
                    captured_at__month=m,
                ).order_by('captured_at')[:1]

                start_time = month + '-01'
                if end_seq.count() == 0 or action == 'restore':
                    if m == '12':
                        y = str(int(y) + 1)
                        m = '01'
                    else:
                        if int(m) < 9:
                            m = '0' + str(int(m) + 1)
                        else:
                            m = str(int(m) + 1)
                    end_time = y + '-' + m + '-01'
                    per_page = 5
                else:
                    end_time = str(end_seq[0].captured_at)[0:19]
                    per_page = 6


                # sequences = []
                # seqs = Sequence.objects.filter()[:5]
                #
                # for s in seqs:
                #     sequences.append(s)

                url = 'https://a.mapillary.com/v3/sequences?page=1&per_page={}&client_id={}&userkeys={}&start_time={}&end_time={}'.format(per_page, settings.MAPILLARY_CLIENT_ID, map_user.key, start_time, end_time)
                # url = 'https://a.mapillary.com/v3/sequences?per_page=1000&client_id={}&start_time={}&end_time={}'.format(settings.MAPILLARY_CLIENT_ID, start_time, end_time)
                response = requests.get(url)
                r = requests.head(url)

                data = response.json()

                for feature in data['features']:
                    properties = feature['properties']
                    geometry = feature['geometry']
                    sequence = Sequence.objects.filter(seq_key=properties['key'])[:1]

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
                    # lineString = LineString(geometry['coordinates'][0], geometry['coordinates'][1])
                    # i = 0
                    # print(time.process_time() - start)
                    # for point in geometry['coordinates']:
                    #     i += 1
                    #     if i < 3:
                    #         continue
                    #     lineString.append((point[0], point[1]))
                    # print('len: ', len(lineString))
                    # sequence.geometry_coordinates = lineString
                    sequence.coordinates_cas = properties['coordinateProperties']['cas']
                    sequence.coordinates_image = properties['coordinateProperties']['image_keys']
                    if 'private' in properties:
                        sequence.is_privated = properties['private']
                    sequence.save()
                    sequences.append(sequence)
            else:
                trash_sequences = Sequence.objects.filter(user_key=map_user.key, is_transport=False, captured_at__month=m, captured_at__year=y)
                paginator = Paginator(trash_sequences.order_by('-created_at'), 5)

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
                print(sequences.count)

    addSequenceForm = AddSequeceForm()
    all_tags = []
    all_transport_types = []
    tags = Tag.objects.filter(is_actived=True)
    for t in tags:
        all_tags.append({'id': t.pk, 'name': t.name})
    transport_types = TransportType.objects.all()
    for type in transport_types:
        all_transport_types.append({'id': type.pk, 'name': type.name})
    content = {
        'search_form': search_form,
        'seq_count': len(sequences),
        'sequences': sequences,
        'pageName': 'Sequences',
        'pageTitle': 'Sequences',
        'pageDescription': IMPORT_PAGE_DESCRIPTION,
        'addSequenceForm': addSequenceForm,
        'all_tags': all_tags,
        'all_transport_types': all_transport_types,
        'action': action,
        'page': page
    }
    return render(request, 'sequence/import_list.html', content)

@my_login_required
def ajax_import(request):
    if request.method == 'POST':
        sequence_str = request.POST.get('sequence_json')
        sequence_json = json.loads(sequence_str)
        for unique_id in sequence_json.keys():
            sequence = Sequence.objects.get(unique_id=unique_id)
            if sequence is None:
                continue
            if sequence_json[unique_id]['name'] == '' or sequence_json[unique_id]['description'] == '' or sequence_json[unique_id]['transport_type'] == 0 or len(sequence_json[unique_id]['tags']) == 0:
                continue
            sequence.name = sequence_json[unique_id]['name']
            sequence.description = sequence_json[unique_id]['description']
            sequence.transport_type_id = sequence_json[unique_id]['transport_type']
            sequence.tag = sequence_json[unique_id]['tags']
            sequence.is_published = True
            sequence.is_transport = True
            print(sequence.name)
            sequence.save()

    return JsonResponse({
        'status': 'success',
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

