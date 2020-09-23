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
from sequence.models import TransType, SequenceLike
## App packages

# That includes from .models import *
from .forms import *
from sequence.forms import SequenceSearchForTourForm

MAIN_PAGE_DESCRIPTION = "Tours are collections of sequences that have been curated by their owner. Browse others' tours or create one using your own sequences."

# Tour
def index(request):
    return redirect('tour.tour_list')

@my_login_required
def tour_create(request, unique_id=None):
    mapillary_users = MapillaryUser.objects.filter(user=request.user)
    if mapillary_users.count() == 0:
        messages.error(request, "You don't have any sequences. Please upload sequence or import from Mapillary.")
        return redirect('sequence.index')
    mapillary_user = mapillary_users[0]
    if request.method == "POST":
        form = TourForm(request.POST)
        if form.is_valid():
            if unique_id is None:
                tour = form.save(commit=False)
                tour.user = request.user
                tour.username = mapillary_user.username
                tour.is_published = False
                tour.save()
                if form.cleaned_data['tour_tag'].count() > 0:
                    for tour_tag in form.cleaned_data['tour_tag']:
                        tour.tour_tag.add(tour_tag)
                    for tour_tag in tour.tour_tag.all():
                        if not tour_tag in form.cleaned_data['tour_tag']:
                            tour.tour_tag.remove(tour_tag)
                messages.success(request, 'A tour was created successfully.')
            else:
                tour = get_object_or_404(Tour, unique_id=unique_id)
                tour.name = form.cleaned_data['name']
                tour.description = form.cleaned_data['description']
                if form.cleaned_data['tour_tag'].count() > 0:
                    for tour_tag in form.cleaned_data['tour_tag']:
                        tour.tour_tag.add(tour_tag)
                    for tour_tag in tour.tour_tag.all():
                        if not tour_tag in form.cleaned_data['tour_tag']:
                            tour.tour_tag.remove(tour_tag)
                tour.save()
                messages.success(request, 'A tour was updated successfully.')

            return redirect('tour.tour_add_sequence', unique_id=tour.unique_id)
    else:
        if unique_id:
            tour = get_object_or_404(Tour, unique_id=unique_id)
            form = TourForm(instance=tour)
        else:
            form = TourForm()
    content = {
        'form': form,
        'pageName': 'Create Tour',
        'pageTitle': 'Create Tour',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
    }
    return render(request, 'tour/create.html', content)

@my_login_required
def tour_add_sequence(request, unique_id):
    tour = get_object_or_404(Tour, unique_id=unique_id)
    sequences = None
    page = 1
    action = 'list'
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        action = request.GET.get('action')
        if action is None:
            action = 'list'

        form = SequenceSearchForTourForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            camera_make = form.cleaned_data['camera_make']
            tags = form.cleaned_data['tag']
            transport_type = form.cleaned_data['transport_type']
            like = form.cleaned_data['like']

            # start_time = form.cleaned_data['start_time']
            # end_time = form.cleaned_data['end_time']
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
        form = SequenceSearchForTourForm()

    sequences = sequences.order_by('-created_at')

    sequence_ary = []
    tour_sequences = TourSequence.objects.filter(tour=tour)
    t_sequence_ary = []
    if tour_sequences.count() > 0:
        for t_s in tour_sequences:
            t_sequence_ary.append(t_s.sequence.unique_id)
    for sequence in sequences:
        if not sequence.unique_id in t_sequence_ary:
            sequence_ary.append(sequence)

    t_form = TourForm(instance=tour)

    if action == 'add':
        # if sequences.count() > 0:
        #     for sequence in sequences:
        #         if not sequence in t_sequence_ary:
        #             sequence_ary.append(sequence)
        #
        # paginator = Paginator(sequence_ary, 5)

        paginator = Paginator(sequence_ary, 5)
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
        content = {
            'sequences': pSequences,
            'sequence_count': len(pSequences),
            'form': form,
            'pageName': 'Edit Tour',
            'pageTitle': tour.name + ' - Edit Tour',
            'pageDescription': MAIN_PAGE_DESCRIPTION,
            'page': page,
            'tour': tour,
            'action': action,
            't_form': t_form,
            't_sequence_ary': t_sequence_ary
        }
        return render(request, 'tour/add_seq.html', content)
    else:
        sequences = sequences.filter(unique_id__in=t_sequence_ary)
        content = {
            'sequences': sequences,
            'sequence_count': len(sequences),
            'form': form,
            'pageName': 'Edit Tour',
            'pageTitle': tour.name + ' - Edit Tour',
            'pageDescription': MAIN_PAGE_DESCRIPTION,
            'page': page,
            'tour': tour,
            'action': action,
            't_form': t_form,
            't_sequence_ary': t_sequence_ary
        }
        return render(request, 'tour/add_seq.html', content)

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
            tags = form.cleaned_data['tour_tag']
            username = form.cleaned_data['username']
            like = form.cleaned_data['like']

            tours = Tour.objects.all().filter(
                is_published=True
            )
            print(tours.count())
            if name and name != '':
                tours = tours.filter(name__contains=name)
            if username and username != '':
                users = CustomUser.objects.filter(username__contains=username)
                tours = tours.filter(user__in=users)
            if len(tags) > 0:
                for tour_tag in tags:
                    tours = tours.filter(tour_tag=tour_tag)
            if like and like != 'all':
                tour_likes = TourLike.objects.all().values('tour').annotate()
                print(tour_likes)
                tour_ary = []
                if tour_likes.count() > 0:
                    for tour_like in tour_likes:
                        tour_ary.append(tour_like['tour'])
                if like == 'true':
                    tours = tours.filter(pk__in=tour_ary)
                elif like == 'false':
                    tours = tours.exclude(pk__in=tour_ary)

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
    content = {
        'tours': pTours,
        'form': form,
        'pageName': 'Tours',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'pageTitle': 'Tours',
        'page': page
    }
    return render(request, 'tour/list.html', content)

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
            tags = form.cleaned_data['tour_tag']
            like = form.cleaned_data['like']
            tours = Tour.objects.all().filter(
                user=request.user
            )
            if name and name != '':
                tours = tours.filter(name__contains=name)
            if len(tags) > 0:
                for tour_tag in tags:
                    tours = tours.filter(tour_tag=tour_tag)
            if like and like != 'all':
                tour_likes = TourLike.objects.all().values('tour').annotate()
                print(tour_likes)
                tour_ary = []
                if tour_likes.count() > 0:
                    for tour_like in tour_likes:
                        tour_ary.append(tour_like['tour'])
                if like == 'true':
                    tours = tours.filter(pk__in=tour_ary)
                elif like == 'false':
                    tours = tours.exclude(pk__in=tour_ary)

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
    form._my(request.user.username)
    content = {
        'tours': pTours,
        'form': form,
        'pageName': 'My Tours',
        'pageTitle': 'My Tours',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page
    }
    return render(request, 'tour/list.html', content)

def tour_detail(request, unique_id):
    tour = get_object_or_404(Tour, unique_id=unique_id)
    sequence_ary = []
    tour_sequences = TourSequence.objects.filter(tour=tour).order_by('sort')
    t_count_ary = []
    if tour_sequences.count() > 0:
        for t_s in tour_sequences:
            t_sequences = TourSequence.objects.filter(sequence=t_s.sequence)
            if t_sequences is None or not t_sequences:
                t_s.sequence.tour_count = 0
            else:
                t_s.sequence.tour_count = t_sequences.count()

            sequence_ary.append(t_s.sequence)

    first_image_key = ''
    if len(sequence_ary) > 0:
        first_image_key = sequence_ary[0].coordinates_image[0]
    content = {
        'sequences': sequence_ary,
        'sequence_count': len(sequence_ary),
        'pageName': 'Tour Detail',
        'pageTitle': tour.name + ' - Tour Detail',
        'pageDescription': tour.description,
        'tour': tour,
        'first_image_key': first_image_key,
        't_count_ary': t_count_ary
    }
    return render(request, 'tour/detail.html', content)

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
            if form.cleaned_data['tour_tag'].count() > 0:
                for tour_tag in form.cleaned_data['tour_tag']:
                    tour.tour_tag.add(tour_tag)
                for tour_tag in tour.tour_tag.all():
                    if not tour_tag in form.cleaned_data['tour_tag']:
                        tour.tour_tag.remove(tour_tag)
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
        'message': 'The tour does not exist or has no access.'
    })


@my_login_required
def tour_delete(request, unique_id):
    tour = get_object_or_404(Tour, unique_id=unique_id)
    if request.method == "POST":
        if tour.user != request.user:
            messages.error(request, 'The tour does not exist or has no access.')
            return redirect('tour.tour_list')

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
        return redirect('tour.tour_list')

    messages.error(request, 'The tour does not exist or has no access.')
    return redirect('tour.tour_list')

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
            messages.success(request, 'Sequence is successfully removed in tour.')
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
            messages.success(request, 'Sequence is successfully added in tour.')
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
