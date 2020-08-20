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

## App packages

# That includes from .models import *
from .forms import * 

############################################################################

def index(request):
    return redirect('sequence.sequence_list')

def transport_sequence(request):
    if request.user.mapillary_access_token == '' or request.user.mapillary_access_token is None:
        return redirect(settings.MAPILLARY_AUTHENTICATION_URL)
    else:
        map_user = get_mapillary_user(request.user.mapillary_access_token)
        if map_user is None:
            return redirect(settings.MAPILLARY_AUTHENTICATION_URL)
        return redirect('sequence.transport_sequence_list')

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
        'pageName': 'sequence-list',
        'page': page
    }
    return render(request, 'sequence/sequence/list.html', content)

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
        'pageName': 'my-sequence-list',
        'page': page
    }
    return render(request, 'sequence/sequence/list.html', content)

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
    print(pImages.count)
    addSequenceForm = AddSequeceForm(instance=sequence)
    content = {
        'sequence': sequence,
        'images': pImages,
        'pageName': 'sequence-detail',
        'page': page,
        'first_image': pImages[0],
        'addSequenceForm': addSequenceForm
    }
    return render(request, 'sequence/sequence/detail.html', content)

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

@my_login_required
def transport_sequence_list(request):
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
        'pageName': 'sequence-list',
        'addSequenceForm': addSequenceForm,
        'all_tags': all_tags,
        'all_transport_types': all_transport_types,
        'action': action,
        'page': page
    }
    return render(request, 'sequence/sequence/transport_list.html', content)

@my_login_required
def ajax_transport(request):
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


# Tour

@my_login_required
def tour_create(request, unique_id=None):
    mapillary_user = MapillaryUser.objects.get(user=request.user)
    if not mapillary_user:
        messages.error(request, "You don't have any sequences. Please upload sequence or transport from Mapillary.")
        return redirect('sequence.index')

    if request.method == "POST":
        form = TourForm(request.POST)
        if form.is_valid():
            if unique_id is None:
                tour = form.save(commit=False)
                tour.user = request.user
                tour.username = mapillary_user.username
                tour.is_published = False
                tour.save()
                print(tour.username)
                messages.success(request, 'A tour was created successfully.')
            else:
                tour = get_object_or_404(Tour, unique_id=unique_id)
                tour.name = form.cleaned_data['name']
                tour.description = form.cleaned_data['description']
                tour.tag = form.cleaned_data['tag']
                tour.save()
                messages.success(request, 'A tour was updated successfully.')

            return redirect('sequence.tour_add_sequence', unique_id=tour.unique_id)
    else:
        if unique_id:
            tour = get_object_or_404(Tour, unique_id=unique_id)
            form = TourForm(instance=tour)
        else:
            form = TourForm()
    return render(request, 'sequence/tour/create.html', {'form': form, 'pageName': 'tour-create'})

@my_login_required
def tour_add_sequence(request, unique_id):
    tour = get_object_or_404(Tour, unique_id=unique_id)
    sequences = None
    page = 1
    action = 'add'
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        action = request.GET.get('action')
        if action is None:
            action = 'add'

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
                sequences = sequences.filter(transport_type_id=transport_type)
            if username and username != '':
                sequences = sequences.filter(username__contains=username)
            if len(tags) > 0:
                sequences = sequences.filter(tag__overlap=tags)

    if sequences == None:
        sequences = Sequence.objects.all().filter(is_published=True, is_approved=True)
        form = SequenceSearchForm()

    sequences = sequences.order_by('-created_at')

    sequence_ary = []
    tour_sequences = TourSequence.objects.filter(tour=tour)
    t_sequence_ary = []
    if tour_sequences.count() > 0:
        for t_s in tour_sequences:
            t_sequence_ary.append(t_s.sequence.unique_id)

    t_form = TourForm(instance=tour)

    if action == 'add':
        # if sequences.count() > 0:
        #     for sequence in sequences:
        #         if not sequence in t_sequence_ary:
        #             sequence_ary.append(sequence)
        #
        # paginator = Paginator(sequence_ary, 5)

        paginator = Paginator(sequences, 5)
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
            'sequence_count': len(pSequences),
            'form': form,
            'pageName': 'search-sequence-list',
            'page': page,
            'tour': tour,
            'action': action,
            't_form': t_form,
            't_sequence_ary': t_sequence_ary
        }
        return render(request, 'sequence/tour/add_seq.html', content)
    else:
        sequences = sequences.filter(unique_id__in=t_sequence_ary)
        content = {
            'sequences': sequences,
            'sequence_count': len(sequences),
            'form': form,
            'pageName': 'search-sequence-list',
            'page': page,
            'tour': tour,
            'action': action,
            't_form': t_form,
            't_sequence_ary': t_sequence_ary
        }
        return render(request, 'sequence/tour/add_seq.html', content)

def tour_list(request):
    tours = None
    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        form = TourSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            tags = form.cleaned_data['tag']
            username = form.cleaned_data['username']

            tours = Tour.objects.all().filter(
                is_published=True
            )
            if name and name != '':
                tours = tours.filter(name__contains=name)
            if username and username != '':
                tours = tours.filter(username__contains=username)
            if len(tags) > 0:
                tours = tours.filter(tag__overlap=tags)

    print(tours)
    if tours == None:
        tours = Tour.objects.all().filter(is_published=True)
        form = TourSearchForm()

    paginator = Paginator(tours.order_by('-created_at'), 5)

    try:
        pTours = paginator.page(page)
    except PageNotAnInteger:
        pTours = paginator.page(1)
    except EmptyPage:
        pTours = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pTours.number < 4:
            first_num = 1
            last_num = 7
        elif pTours.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pTours.number - 3
            last_num = pTours.number + 3
    pTours.paginator.pages = range(first_num, last_num + 1)
    pTours.count = len(pTours)
    print(pTours.count)
    content = {
        'tours': pTours,
        'form': form,
        'pageName': 'tour-list',
        'page': page
    }
    return render(request, 'sequence/tour/list.html', content)

@my_login_required
def my_tour_list(request):
    tours = None
    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        form = TourSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            tags = form.cleaned_data['tag']
            username = form.cleaned_data['username']

            tours = Tour.objects.all().filter(
                user=request.user
            )
            if name and name != '':
                tours = tours.filter(name__contains=name)
            if username and username != '':
                tours = tours.filter(username__contains=username)
            if len(tags) > 0:
                tours = tours.filter(tag__overlap=tags)

    print(tours)
    if tours == None:
        tours = Tour.objects.all().filter(is_published=True)
        form = TourSearchForm()

    paginator = Paginator(tours.order_by('-created_at'), 5)

    try:
        pTours = paginator.page(page)
    except PageNotAnInteger:
        pTours = paginator.page(1)
    except EmptyPage:
        pTours = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pTours.number < 4:
            first_num = 1
            last_num = 7
        elif pTours.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pTours.number - 3
            last_num = pTours.number + 3
    pTours.paginator.pages = range(first_num, last_num + 1)
    pTours.count = len(pTours)
    print(pTours.count)
    content = {
        'tours': pTours,
        'form': form,
        'pageName': 'my-tour-list',
        'page': page
    }
    return render(request, 'sequence/tour/list.html', content)

def tour_detail(request, unique_id):
    tour = get_object_or_404(Tour, unique_id=unique_id)
    sequence_ary = []
    tour_sequences = TourSequence.objects.filter(tour=tour).order_by('sort')
    t_sequence_ary = []
    if tour_sequences.count() > 0:
        for t_s in tour_sequences:
            sequence_ary.append(t_s.sequence)
            t_sequence_ary.append(t_s.sequence.unique_id)

    first_image_key = ''
    if len(sequence_ary) > 0:
        first_image_key = sequence_ary[0].coordinates_image[0]
    content = {
        'sequences': sequence_ary,
        'sequence_count': len(sequence_ary),
        'pageName': 'search-sequence-list',
        'tour': tour,
        'first_image_key': first_image_key,
        't_sequence_ary': t_sequence_ary
    }
    return render(request, 'sequence/tour/detail.html', content)

@my_login_required
def ajax_tour_update(request, unique_id=None):
    if request.method == "POST":
        form = TourForm(request.POST)

        if form.is_valid():
            tour = Tour.objects.get(unique_id=unique_id)
            if not tour:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The tour does not exist or has no access.'
                })

            tour.name = form.cleaned_data['name']
            tour.description = form.cleaned_data['description']
            tour.tag = form.cleaned_data['tag']
            tour.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Tour was uploaded successfully.',
                'tour': {
                    'name': tour.name,
                    'description': tour.description,
                    'tag': tour.getTags()
                }
            })

    return JsonResponse({
        'status': 'failed',
        'message': 'The tour does not exist or has no access.'
    })


@my_login_required
def tour_delete(request, unique_id):
    tour = get_object_or_404(Tour, unique_id=unique_id)
    if request.method == "POST":
        if tour.user != request.user:
            messages.error(request, 'The tour does not exist or has no access.')
            return redirect('sequence.tour_list')

        name = tour.name

        sequences = TourSequence.objects.filter(tour=tour)

        if sequences.count() > 0:
            for seq in sequences:
                seq.delete()

        tour_likes = TourLike.objects.filter(tour=tour)

        if tour_likes.count() > 0:
            for t_like in tour_likes:
                t_like.delete()

        tour.delete()

        messages.success(request, 'Tour "{}" is deleted successfully.'.format(name))
        return redirect('sequence.tour_list')

    messages.error(request, 'The tour does not exist or has no access.')
    return redirect('sequence.tour_list')

def ajax_change_tour_seq(request, unique_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': 'The tour does not exist or has no access.'
        })
    tour = Tour.objects.get(unique_id=unique_id)
    if not tour or tour is None or tour.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'The tour does not exist or has no access.'
        })

    if request.method == "POST":
        sequence_id = request.POST.get('sequence_unique_id')
        sequence = Sequence.objects.get(unique_id=sequence_id)
        if not sequence or sequence is None or sequence.user != request.user:
            return JsonResponse({
                'status': 'failed',
                'message': 'The Sequence does not exist or has no access.'
            })

        tour_sequence = TourSequence.objects.filter(tour=tour, sequence=sequence)[:1]
        if tour_sequence.count() > 0:
            tour_sequence[0].delete()
            return JsonResponse({
                'status': 'success',
                'message': 'The "{}" was removed from "{}"'.format(sequence.name, tour.name),
                'action': 'removed'
            })
        else:
            tour_sequence = TourSequence()
            tour_sequence.tour = tour
            tour_sequence.sequence = sequence

            sequences = TourSequence.objects.filter(tour=tour)
            max_sort = 0
            if sequences.count() > 0:
                for s in sequences:
                    if s.sort > max_sort:
                        max_sort = s.sort
            tour_sequence.sort = max_sort + 1
            tour_sequence.save()
            return JsonResponse({
                'status': 'success',
                'message': 'The "{}" was added in "{}"'.format(sequence.name, tour.name),
                'action': 'added'
            })

    return JsonResponse({
        'status': 'failed',
        'message': 'The Sequence does not exist or has no access.'
    })

def ajax_order_sequence(request, unique_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': 'The tour does not exist or has no access.'
        })
    tour = Tour.objects.get(unique_id=unique_id)
    if not tour or tour is None or tour.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'The tour does not exist or has no access.'
        })

    if request.method == "POST":
        order_str = request.POST.get('order_list')
        order_list = order_str.split(',')
        tour_seq_list = []
        for i in range(len(order_list)):
            print(str(i) + ': ' + order_list[i])
            sequence = Sequence.objects.get(unique_id=order_list[i])
            if sequence is None or sequence.user != request.user:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The sequence does not exist or has no access.'
                })
            tour_sequence = TourSequence.objects.filter(tour=tour, sequence=sequence)[:1]
            if tour_sequence.count() == 0:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The sequence does not exist or has no access.'
                })

            tour_seq_list.append(tour_sequence[0])
        for i in range(len(order_list)):
            tour_seq_list[i].sort = i
            tour_seq_list[i].save()

        return JsonResponse({
            'status': 'success',
            'message': 'Sequences were ordered successfully.'
        })

    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to order sequence!'
    })

def ajax_tour_check_publish(request, unique_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't change the status."
        })

    tour = Tour.objects.get(unique_id=unique_id)
    if not tour:
        return JsonResponse({
            'status': 'failed',
            'message': 'The tour does not exist.'
        })

    if tour.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'This tour is not created by you.'
        })

    if tour.is_published:
        tour.is_published = False
        message = 'Unpublished'
    else:
        tour.is_published = True
        message = 'Published'
    tour.save()
    return JsonResponse({
        'status': 'success',
        'message': message,
        'is_published': tour.is_published
    })

def ajax_tour_check_like(request, unique_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't change the status."
        })

    tour = Tour.objects.get(unique_id=unique_id)
    if not tour:
        return JsonResponse({
            'status': 'failed',
            'message': 'The tour does not exist.'
        })

    if tour.user == request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'This tour is created by you.'
        })

    tour_like = TourLike.objects.filter(tour=tour, user=request.user)
    if tour_like:
        for g in tour_like:
            g.delete()
        liked_tour = TourLike.objects.filter(tour=tour)
        if not liked_tour:
            liked_count = 0
        else:
            liked_count = liked_tour.count()
        return JsonResponse({
            'status': 'success',
            'message': 'Unliked',
            'is_checked': False,
            'liked_count': liked_count
        })
    else:
        tour_like = TourLike()
        tour_like.tour = tour
        tour_like.user = request.user
        tour_like.save()
        liked_tour = TourLike.objects.filter(tour=tour)
        if not liked_tour:
            liked_count = 0
        else:
            liked_count = liked_tour.count()
        return JsonResponse({
            'status': 'success',
            'message': 'Liked',
            'is_checked': True,
            'liked_count': liked_count
        })
