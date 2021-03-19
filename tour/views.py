# Python packages
import json

from django.contrib import messages
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import (
    JsonResponse, )
## Django Packages
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

## Project packages
from accounts.models import CustomUser, MapillaryUser
## Custom Libs ##
from lib.functions import *
from lib.django_db_functions import get_correct_sql
from sequence.forms import SequenceSearchForTourForm
from sequence.models import TransType, SequenceLike
# That includes from .models import *
from .forms import *

# App packages

MAIN_PAGE_DESCRIPTION = "Tours are collections of sequences that have been curated by their owner. Browse others' tours or create one using your own sequences."


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

                sequence_unique_id = request.GET.get('sequence_unique_id', None)
                if sequence_unique_id is not None:
                    sequence = Sequence.objects.get(unique_id=sequence_unique_id)
                    if sequence is not None:
                        tour_sequence = TourSequence()
                        tour_sequence.sequence = sequence
                        tour_sequence.tour = tour

                        max_sort_ts = TourSequence.objects.filter(sequence=sequence, tour=tour).order_by('-sort').first()
                        if max_sort_ts is None:
                            max_sort = 0
                        else:
                            max_sort = max_sort_ts.sort

                        tour_sequence.sort = max_sort + 1
                        tour_sequence.save()

                        tour.is_published = True
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
                        if tour_tag not in form.cleaned_data['tour_tag']:
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
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            # start_time = form.cleaned_data['start_time']
            # end_time = form.cleaned_data['end_time']
            sequences = Sequence.objects.all().filter(
                user=request.user
            ).exclude(image_count=0)
            if name and name != '':
                sequences = sequences.filter(name__icontains=name)
            if camera_make is not None and len(camera_make) > 0:
                sequences = sequences.filter(camera_make__name__in=camera_make)
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
                print(sequence_likes)
                sequence_ary = []
                if sequence_likes.count() > 0:
                    for sequence_like in sequence_likes:
                        sequence_ary.append(sequence_like['sequence'])
                if like == 'true':
                    sequences = sequences.filter(pk__in=sequence_ary)
                elif like == 'false':
                    sequences = sequences.exclude(pk__in=sequence_ary)

            if start_time is not None and start_time != '':
                sequences = sequences.filter(captured_at__gte=start_time)

            if end_time is not None and end_time != '':
                sequences = sequences.filter(captured_at__lte=end_time)


    if sequences is None:
        sequences = Sequence.objects.all().filter(is_published=True).exclude(image_count=0)
        form = SequenceSearchForTourForm()

    sequences = sequences.order_by('-captured_at')

    sequence_ary = []
    tour_sequences = TourSequence.objects.filter(tour=tour).order_by('sort')
    t_sequence_ary = []
    if tour_sequences.count() > 0:
        for t_s in tour_sequences:
            t_sequence_ary.append(t_s.sequence.unique_id)
    for sequence in sequences:
        if sequence.unique_id not in t_sequence_ary:
            sequence_ary.append(sequence)

    t_form = TourForm(instance=tour)

    if action == 'add':
        # if sequences.count() > 0:
        #     for sequence in sequences:
        #         if not sequence in t_sequence_ary:
        #             sequence_ary.append(sequence)
        #
        # paginator = Paginator(sequence_ary, 5)

        paginator = Paginator(sequence_ary, 10)
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
        sequences = []
        for t_s in t_sequence_ary:
            seq = Sequence.objects.filter(unique_id=t_s).first()
            if seq is not None and seq:
                tour_sequences = TourSequence.objects.filter(sequence=seq)
                if tour_sequences is None or not tour_sequences:
                    seq.tour_count = 0
                else:
                    seq.tour_count = tour_sequences.count()
                sequences.append(seq)
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
    order_type = 'latest_at'
    is_filtered = False
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        order_type = request.GET.get('order_type')
        form = TourSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            tags = form.cleaned_data['tour_tag']
            username = form.cleaned_data['username']
            like = form.cleaned_data['like']

            tours = Tour.objects.all().filter(
                is_published=True
            )

            sequence_key = request.GET.get('sequence_key')
            if not sequence_key is None and sequence_key != '':
                t_s = TourSequence.objects.filter(sequence__seq_key=sequence_key)
                t_ids = []
                if t_s.count() > 0:
                    for t in t_s:
                        t_ids.append(t.tour.pk)
                tours = tours.filter(pk__in=t_ids)
                is_filtered = True

            if name and name != '':
                tours = tours.filter(name__icontains=name)
                is_filtered = True
            if username and username != '':
                users = CustomUser.objects.filter(username__icontains=username)
                tours = tours.filter(user__in=users)
                is_filtered = True
            if len(tags) > 0:
                for tour_tag in tags:
                    tours = tours.filter(tour_tag=tour_tag)
                is_filtered = True
            if like and like != 'all':
                tour_likes = TourLike.objects.all().values('tour').annotate()
                tour_ary = []
                if tour_likes.count() > 0:
                    for tour_like in tour_likes:
                        tour_ary.append(tour_like['tour'])
                if like == 'true':
                    tours = tours.filter(pk__in=tour_ary)
                elif like == 'false':
                    tours = tours.exclude(pk__in=tour_ary)
                is_filtered = True

            sequence_unique_id = request.GET.get('sequence_unique_id')
            if sequence_unique_id is not None and sequence_unique_id != '':
                try:
                    sequences = Sequence.objects.filter(unique_id=sequence_unique_id)[:1]
                    if sequences.count() > 0:
                        sequence = sequences[0]
                        tour_sequences = TourSequence.objects.filter(sequence=sequence)
                        tours = tours.filter(pk__in=tour_sequences.values_list('tour_id'))
                except:
                    messages.error(request, 'Sequence Unique Id is not a valid UUID.')
                    return redirect('home')

    if tours is None:
        tours = Tour.objects.all().filter(is_published=True)
        form = TourSearchForm()

    request.session['tours_query'] = get_correct_sql(tours)
    print(order_type)

    if order_type == 'most_likes':
        paginator = Paginator(tours.order_by('-like_count', '-created_at'), 10)
    else:
        paginator = Paginator(tours.order_by('-created_at'), 10)

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
        'is_filtered': is_filtered,
        'page': page,
        'order_type': order_type
    }
    return render(request, 'tour/list.html', content)


@my_login_required
def my_tour_list(request):
    tours = None
    page = 1
    order_type = 'latest_at'
    is_filtered = False
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        order_type = request.GET.get('order_type')
        form = TourSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            tags = form.cleaned_data['tour_tag']
            like = form.cleaned_data['like']

            tours = Tour.objects.all().filter(
                user=request.user
            )
            if name and name != '':
                tours = tours.filter(name__icontains=name)
                is_filtered = True
            if len(tags) > 0:
                for tour_tag in tags:
                    tours = tours.filter(tour_tag=tour_tag)
                is_filtered = True
            if like and like != 'all':
                tour_likes = TourLike.objects.all().values('tour').annotate()
                tour_ary = []
                if tour_likes.count() > 0:
                    for tour_like in tour_likes:
                        tour_ary.append(tour_like['tour'])
                if like == 'true':
                    tours = tours.filter(pk__in=tour_ary)
                elif like == 'false':
                    tours = tours.exclude(pk__in=tour_ary)
                is_filtered = True

    if tours is None:
        tours = Tour.objects.all().filter(is_published=True)
        form = TourSearchForm()

    request.session['tours_query'] = get_correct_sql(tours)

    if order_type == 'most_likes':
        paginator = Paginator(tours.order_by('-like_count', '-created_at'), 10)
    else:
        paginator = Paginator(tours.order_by('-created_at'), 10)

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
        'is_filtered': is_filtered,
        'page': page,
        'order_type': order_type

    }
    return render(request, 'tour/list.html', content)


def tour_detail(request, unique_id):
    tour = get_object_or_404(Tour, unique_id=unique_id)
    if not tour.is_published and request.user != tour.user:
        messages.error(request, 'The tour is not published.')
        return redirect('tour.index')
    page = request.GET.get('page')
    if page is None:
        page = 1
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
    firstImageKey = ''
    if len(sequence_ary) > 0:
        first_image_key = sequence_ary[0].coordinates_image[0]
        firstImageKey = sequence_ary[0].get_first_image_key()

    paginator = Paginator(sequence_ary, 10)

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

    request.session['tour_detail_id'] = tour.id

    content = {
        'sequences': pItems,
        'sequence_count': len(sequence_ary),
        'pageName': 'Tour Detail',
        'pageTitle': tour.name + ' - Tour Detail',
        'pageDescription': tour.description,
        'tour': tour,
        'first_image_key': first_image_key,
        't_count_ary': t_count_ary,
        'firstImageKey': firstImageKey,
        'page': page
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
                    'tag': tour.get_tags()
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
            if TourSequence.objects.filter(tour=tour).count() == 1:
                tour.is_published = True
                tour.save()
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

    if not tour.is_published:
        return JsonResponse({
            'status': 'failed',
            'message': "This tour is not published."
        })

    tour_like = TourLike.objects.filter(tour=tour, user=request.user)
    if tour_like:
        if tour.user.is_liked_email:
            # confirm email
            try:
                # send email to creator
                subject = 'Your Map the Paths Tour Was Liked'
                html_message = render_to_string(
                    'emails/tour/like.html',
                    {'subject': subject, 'like': 'unliked', 'tour': tour, 'sender': request.user},
                    request
                )
                send_mail_with_html(subject, html_message, tour.user.email, settings.SMTP_REPLY_TO)
            except:
                print('email sending error!')
        for g in tour_like:
            g.delete()
        liked_tour = TourLike.objects.filter(tour=tour)
        if not liked_tour:
            liked_count = 0
        else:
            liked_count = liked_tour.count()
        tour.like_count = liked_count
        tour.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Unliked',
            'is_checked': False,
            'liked_count': liked_count
        })
    else:
        if tour.user.is_liked_email:
            # confirm email
            try:
                # send email to creator
                subject = 'Your Map the Paths Tour Was Liked'
                html_message = render_to_string(
                    'emails/tour/like.html',
                    {'subject': subject, 'like': 'liked', 'tour': tour, 'sender': request.user},
                    request
                )
                send_mail_with_html(subject, html_message, tour.user.email, settings.SMTP_REPLY_TO)
            except:
                print('email sending error!')
        tour_like = TourLike()
        tour_like.tour = tour
        tour_like.user = request.user
        tour_like.save()
        liked_tour = TourLike.objects.filter(tour=tour)
        if not liked_tour:
            liked_count = 0
        else:
            liked_count = liked_tour.count()
        tour.like_count = liked_count
        tour.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Liked',
            'is_checked': True,
            'liked_count': liked_count
        })


def ajax_get_detail(request, unique_id):
    tour = Tour.objects.get(unique_id=unique_id)
    if tour.user == request.user:
        is_mine = True
    else:
        is_mine = False
    serialized_obj = serializers.serialize('json', [tour, ])
    data = {
        'tour': json.loads(serialized_obj)
    }

    if not data['tour']:
        data['message'] = "The tour id doesn't exist."
    else:
        data['tour_html_detail'] = render_to_string('tour/modal_detail.html', {'tour': tour, 'is_mine': is_mine})

    return JsonResponse(data)


def ajax_get_detail_by_image_key(request, image_key):
    print(image_key)
    sequences = Sequence.objects.filter(coordinates_image__contains=[image_key])
    print(sequences.count())
    if sequences.count() == 0:
        return JsonResponse({
            'status': 'failed',
            'message': "Not imported from Mapillary."
        })

    tours = []
    data = {}

    tour_sequences = TourSequence.objects.filter(sequence=sequences[0])

    for tour_sequence in tour_sequences:
        tours.append(tour_sequence.tour)

    data['tour_html_detail'] = render_to_string('tour/modal_detail.html', {'tours': tours})

    return JsonResponse(data)
