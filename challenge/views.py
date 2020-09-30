## Python packages
from datetime import datetime
import json

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
from django.contrib.gis.geos import Point, Polygon, MultiPolygon, LinearRing, LineString
from sequence.models import Sequence, Image, ImageLabel
from django.db.models.expressions import F, Window
from django.db.models.functions.window import RowNumber
from django.db.models import Avg, Count, Min, Sum
from datetime import datetime
## Custom Libs ##
from lib.functions import *

## Project packages
from accounts.models import CustomUser

## App packages

# That includes from .models import *
from .forms import *

############################################################################

# def handler404(request, *args, **argv):
#     response = render(request, '404.html', {})
#     response.status_code = 404
#     return response

# def handler500(request, *args, **argv):
#     response = render(request, '500.html', {})
#     response.status_code = 500
#     return response

############################################################################

MAIN_PAGE_DESCRIPTION = "Find or offer help on image collection projects to create fresh street level map data in locations where it's needed for Google Street View, Mapillary, and more..."
JOB_PAGE_DESCRIPTION = ""


############################################################################

def index(request):
    return redirect('challenge.challenge_list')

@my_login_required
def challenge_create(request):
    if request.method == "POST":
        form = ChallengeForm(request.POST)

        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.user = request.user
            geometry = json.loads(challenge.geometry)

            multipoly = MultiPolygon()
            for geo in geometry:
                coordinates = geo['geometry']['coordinates'][0]
                lineString = LineString()
                firstPoint = None
                for i in range(len(coordinates)):
                    coor = coordinates[i]
                    if i == 0:
                        firstPoint = Point(coor[0], coor[1])
                        continue
                    point = Point(coor[0], coor[1])
                    if i == 1:
                        lineString = LineString(firstPoint.coords, point.coords)
                    else:
                        lineString.append(point.coords)
                polygon = Polygon(lineString.coords)
                multipoly.append(polygon)
            challenge.multipolygon = multipoly

            for geo in geometry:
                geo['properties']['challenge_id'] = str(challenge.unique_id)
            challenge.geometry = json.dumps(geometry)

            challenge.save()
            camera_make = form.cleaned_data['camera_make']
            if not camera_make is None and len(camera_make) > 0:
                for cm in camera_make:
                    challenge.camera_make.add(cm)

            transport_type = form.cleaned_data['transport_type']
            if not transport_type is None:
                challenge.transport_type.clear()
                if len(transport_type) > 0:
                    for transport_t in transport_type:
                        challenge.transport_type.add(transport_t)

            messages.success(request, 'A challenge was created successfully.')

            return redirect('challenge.my_challenge_list')
    else:
        form = ChallengeForm()
    content = {
        'form': form,
        'pageName': 'Create Challenge',
        'pageTitle': 'Create Challenge'
    }
    return render(request, 'challenge/capture/create.html', content)

@my_login_required
def challenge_edit(request, unique_id):
    challenge = get_object_or_404(Challenge, unique_id=unique_id)
    if request.method == "POST":
        form = ChallengeForm(request.POST, instance=challenge)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.user = request.user
            challenge.updated_at = datetime.now()
            challenge.save()

            camera_make = form.cleaned_data['camera_make']
            print(camera_make)
            if not camera_make is None and len(camera_make) > 0:
                challenge.transport_type.clear()
                for cm in camera_make:
                    challenge.camera_make.add(cm)

            geometry = json.loads(challenge.geometry)

            multipoly = MultiPolygon()
            for geo in geometry:
                coordinates = geo['geometry']['coordinates'][0]
                lineString = LineString()
                firstPoint = None
                for i in range(len(coordinates)):
                    coor = coordinates[i]
                    if i == 0:
                        firstPoint = Point(coor[0], coor[1])
                        continue
                    point = Point(coor[0], coor[1])
                    if i == 1:
                        lineString = LineString(firstPoint.coords, point.coords)
                    else:
                        lineString.append(point.coords)
                polygon = Polygon(lineString.coords)
                multipoly.append(polygon)
            challenge.multipolygon = multipoly

            for geo in geometry:
                geo['properties']['challenge_id'] = str(challenge.unique_id)
            challenge.geometry = json.dumps(geometry)
            challenge.save()
            transport_type = form.cleaned_data['transport_type']
            print(transport_type.count())
            if not transport_type is None:
                challenge.transport_type.clear()
                for transport_t in transport_type:
                    challenge.transport_type.add(transport_t)
            messages.success(request, 'Challenge "%s" is updated successfully.' % challenge.name)
            return redirect('challenge.index')
    else:
        form = ChallengeForm(instance=challenge)
    content = {
        'form': form,
        'pageName': 'Edit Challenge',
        'challenge': challenge,
        'pageTitle': challenge.name + ' - Edit Challenge'
    }
    return render(request, 'challenge/capture/edit.html', content)

@my_login_required
def my_challenge_delete(request, unique_id):
    challenge = get_object_or_404(Challenge, unique_id=unique_id)
    if challenge.user == request.user:
        challenge.camera_make.clear()
        challenge.transport_type.clear()
        challenge.delete()
        messages.success(request, 'Challenge "%s" is deleted successfully.' % challenge.name)
    else:
        messages.error(request, "This user hasn't permission")

    return redirect('challenge.index')

def challenge_list(request):
    challenges = None
    page = 1
    if request.method == "GET":
        form = ChallengeSearchForm(request.GET)
        page = request.GET.get('page')
        if page is None:
            page = 1
        if form.is_valid():
            challenges = Challenge.objects.all().filter(is_published=True)
            name = form.cleaned_data['name']
            transport_type = form.cleaned_data['transport_type']
            camera_makes = form.cleaned_data['camera_make']
            challenge_type = form.cleaned_data['challenge_type']

            if not name is None:
                challenges = challenges.filter(name__contains=name)
            if not transport_type is None and transport_type != 0 and transport_type != '':
                children_trans_type = TransType.objects.filter(parent_id=transport_type)
                if children_trans_type.count() > 0:
                    types = []
                    types.append(transport_type)
                    for t in children_trans_type:
                        types.append(t.pk)
                    challenges = challenges.filter(transport_type_id__in=types)
                else:
                    challenges = challenges.filter(transport_type=transport_type)

            current_time = datetime.now()
            if not challenge_type is None and challenge_type == 'active':
                challenges = challenges.filter(end_time__gte=current_time)
            if not challenge_type is None and challenge_type == 'completed':
                challenges = challenges.filter(end_time__lt=current_time)
            if not camera_makes is None and len(camera_makes) > 0:
                cs = Challenge.objects.filter(camera_make__in=camera_makes)
                challenges = challenges.filter(pk__in=cs)

    if challenges == None:
        challenges = Challenge.objects.all().filter(is_published=True)
        form = ChallengeSearchForm()

    paginator = Paginator(challenges.order_by('-created_at'), 5)

    try:
        pChallenges = paginator.page(page)
    except PageNotAnInteger:
        pChallenges = paginator.page(1)
    except EmptyPage:
        pChallenges = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pChallenges.number < 4:
            first_num = 1
            last_num = 7
        elif pChallenges.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pChallenges.number - 3
            last_num = pChallenges.number + 3
    pChallenges.paginator.pages = range(first_num, last_num + 1)
    pChallenges.count = len(pChallenges)

    content = {
        'challenges': pChallenges,
        'form': form,
        'pageName': 'Challenges',
        'pageTitle': 'Challenges',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page
    }

    return render(request, 'challenge/capture/list.html', content)

@my_login_required
def my_challenge_list(request):
    challenges = None
    page = 1
    if request.method == "GET":
        form = ChallengeSearchForm(request.GET)
        page = request.GET.get('page')
        if page is None:
            page = 1
        if form.is_valid():
            challenges = Challenge.objects.all().filter(user=request.user)

            name = form.cleaned_data['name']
            transport_type = form.cleaned_data['transport_type']
            camera_makes = form.cleaned_data['camera_make']

            if not name is None:
                challenges = challenges.filter(name__contains=name)
            if not transport_type is None and transport_type != 0 and transport_type != '':
                children_trans_type = TransType.objects.filter(parent_id=transport_type)
                if children_trans_type.count() > 0:
                    types = []
                    types.append(transport_type)
                    for t in children_trans_type:
                        types.append(t)
                    challenges = challenges.filter(transport_type__in=types)
                else:
                    challenges = challenges.filter(transport_type=transport_type)

            challenge_type = form.cleaned_data['challenge_type']
            current_time = datetime.now()
            if not challenge_type is None and challenge_type == 'active':
                challenges = challenges.filter(end_time__gte=current_time)
            if not challenge_type is None and challenge_type == 'completed':
                challenges = challenges.filter(end_time__lt=current_time)
            if not camera_makes is None and len(camera_makes) > 0:

                challenges = challenges.filter(camera_make__in=camera_makes)

    if challenges == None:
        challenges = Challenge.objects.all().filter(user=request.user)
        form = ChallengeSearchForm()

    paginator = Paginator(challenges.order_by('-created_at'), 5)

    try:
        pChallenges = paginator.page(page)
    except PageNotAnInteger:
        pChallenges = paginator.page(1)
    except EmptyPage:
        pChallenges = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pChallenges.number < 4:
            first_num = 1
            last_num = 7
        elif pChallenges.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pChallenges.number - 3
            last_num = pChallenges.number + 3
    pChallenges.paginator.pages = range(first_num, last_num + 1)
    pChallenges.count = len(pChallenges)
    content = {
        'challenges': pChallenges,
        'form': form,
        'pageName': 'My Challenges',
        'pageTitle': 'My Challenges',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page
    }
    return render(request, 'challenge/capture/list.html', content)

def challenge_detail(request, unique_id):
    challenge = get_object_or_404(Challenge, unique_id=unique_id)

    if (not request.user.is_authenticated or request.user != challenge.user) and not challenge.is_published:
        messages.success(request, "You can't access this challenge.")
        return redirect('challenge.challenge_list')

    form = ChallengeSearchForm(request.GET)

    geometry = json.dumps(challenge.geometry)

    page = 1

    if challenge.user == request.user:
        is_mine = True
    else:
        is_mine = False

    challenge_html_detail = render_to_string('challenge/capture/modal_detail.html', {'challenge': challenge, 'is_mine': is_mine})

    return render(request, 'challenge/capture/challenge_detail.html',
          {
              'challenge': challenge,
              'challenge_html_detail': challenge_html_detail,
              'form': form,
              'geometry': geometry,
              'pageName': 'Challenge Detail',
              'pageTitle': challenge.name + ' - Challenge',
              'page': page
          })

def challenge_leaderboard(request, unique_id):
    challenge = get_object_or_404(Challenge, unique_id=unique_id)

    if (not request.user.is_authenticated or request.user != challenge.user) and not challenge.is_published:
        messages.success(request, "You can't access this challenge.")
        return redirect('challenge.challenge_list')

    sequences = Sequence.objects.filter(is_published=True, geometry_coordinates__intersects=challenge.multipolygon)

    cm = challenge.camera_make.all()
    if cm.count() > 0:
        sequences = sequences.filter(camera_make__in=cm)
    print(sequences.count())

    user_json = sequences.values('user').annotate(image_count=Sum('image_count')).order_by('-image_count').annotate(rank=Window(expression=RowNumber()))

    paginator = Paginator(user_json, 10)
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
    print(challenge.transport_type)
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
    form = ChallengeSearchForm(request.GET)

    for i in range(len(pItems)):
        user = CustomUser.objects.get(pk=pItems[i]['user'])

        if user is None or not user:
            continue
        pItems[i]['username'] = user.username

        u_sequences = Sequence.objects.filter(
            user=user
        )

        u_distance = 0
        if u_sequences.count() > 0:
            for u_s in u_sequences:
                u_distance += float(u_s.getDistance())
        pItems[i]['distance'] = "%.3f" % u_distance


    return render(request, 'challenge/capture/leaderboard.html',
          {
              'items': pItems,
              'challenge': challenge,
              'form': form,
              'pageName': 'Challenge Leaderboard',
              'pageTitle': challenge.name + ' - Challenge Leaderboard',
              'page': page
          })

def ajax_challenge_detail(request, unique_id):
    challenge = Challenge.objects.get(unique_id=unique_id)
    if challenge.user == request.user:
        is_mine = True
    else:
        is_mine = False
    serialized_obj = serializers.serialize('json', [challenge, ])
    data = {
        'challenge': json.loads(serialized_obj)
    }

    if not data['challenge']:
        data['error_message'] = "The challenge id doesn't exist."
    else:
        data['challenge_html_detail'] = render_to_string('challenge/capture/modal_detail.html', {'challenge': challenge, 'is_mine': is_mine})

    return JsonResponse(data)









@my_login_required
def label_challenge_create(request):
    if request.method == "POST":
        form = LabelChallengeForm(request.POST)

        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.user = request.user
            geometry = json.loads(challenge.geometry)

            multipoly_ary = []
            for geo in geometry:
                coordinates = geo['geometry']['coordinates']
                print(coordinates)
                multipoly_ary.append(Polygon(coordinates[0]))

            challenge.multipolygon = MultiPolygon(multipoly_ary)

            for geo in geometry:
                geo['properties']['challenge_id'] = str(challenge.unique_id)
            challenge.geometry = json.dumps(geometry)

            challenge.save()
            label_type = form.cleaned_data['label_type']
            if not label_type is None and len(label_type) > 0:
                for lt in label_type:
                    challenge.label_type.add(lt)

            messages.success(request, 'A label challenge was created successfully.')

            return redirect('challenge.my_label_challenge_list')
    else:
        form = LabelChallengeForm()
    content = {
        'form': form,
        'pageName': 'Create Label Challenge',
        'pageTitle': 'Create Label Challenge'
    }
    return render(request, 'challenge/label/create.html', content)

@my_login_required
def label_challenge_edit(request, unique_id):
    challenge = get_object_or_404(LabelChallenge, unique_id=unique_id)
    if request.method == "POST":
        form = LabelChallengeForm(request.POST, instance=challenge)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.user = request.user
            challenge.updated_at = datetime.now()
            challenge.save()

            geometry = json.loads(challenge.geometry)

            multipoly_ary = []
            for geo in geometry:
                coordinates = geo['geometry']['coordinates']
                print(coordinates)
                multipoly_ary.append(Polygon(coordinates[0]))

            challenge.multipolygon = MultiPolygon(multipoly_ary)

            for geo in geometry:
                geo['properties']['challenge_id'] = str(challenge.unique_id)
            challenge.geometry = json.dumps(geometry)
            challenge.save()

            label_type = form.cleaned_data['label_type']
            if not label_type is None:
                challenge.label_type.clear()
                for label_t in label_type:
                    challenge.label_type.add(label_t)
            messages.success(request, 'Challenge "%s" is updated successfully.' % challenge.name)
            return redirect('challenge.label_challenge_list')
    else:
        form = LabelChallengeForm(instance=challenge)
    content = {
        'form': form,
        'pageName': 'Edit Label Challenge',
        'challenge': challenge,
        'pageTitle': challenge.name + ' - Edit Label Challenge'
    }
    return render(request, 'challenge/label/edit.html', content)

@my_login_required
def my_label_challenge_delete(request, unique_id):
    challenge = get_object_or_404(LabelChallenge, unique_id=unique_id)
    if challenge.user == request.user:
        challenge.label_type.clear()
        challenge.delete()
        messages.success(request, 'Challenge "%s" is deleted successfully.' % challenge.name)
    else:
        messages.error(request, "This user hasn't permission")

    return redirect('challenge.label_challenge_list')

def label_challenge_list(request):
    challenges = None
    page = 1
    if request.method == "GET":
        form = LabelChallengeSearchForm(request.GET)
        page = request.GET.get('page')
        if page is None:
            page = 1
        if form.is_valid():
            challenges = LabelChallenge.objects.all().filter(is_published=True)
            name = form.cleaned_data['name']
            labe_type = form.cleaned_data['label_type']
            challenge_type = form.cleaned_data['challenge_type']

            if not name is None:
                challenges = challenges.filter(name__contains=name)
            print(labe_type)
            if not labe_type is None and labe_type != 0 and labe_type != '':
                children_label_type = LabelType.objects.filter(parent_id=labe_type)
                if children_label_type.count() > 0:
                    types = []
                    types.append(labe_type)
                    for t in children_label_type:
                        types.append(t.pk)
                    challenges = challenges.filter(label_type_id__in=types)
                else:
                    challenges = challenges.filter(label_type=labe_type)

            current_time = datetime.now()
            if not challenge_type is None and challenge_type == 'active':
                challenges = challenges.filter(end_time__gte=current_time)
            if not challenge_type is None and challenge_type == 'completed':
                challenges = challenges.filter(end_time__lt=current_time)


    if challenges == None:
        challenges = LabelChallenge.objects.all().filter(is_published=True)
        form = LabelChallengeSearchForm()

    paginator = Paginator(challenges.order_by('-created_at'), 5)

    try:
        pChallenges = paginator.page(page)
    except PageNotAnInteger:
        pChallenges = paginator.page(1)
    except EmptyPage:
        pChallenges = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pChallenges.number < 4:
            first_num = 1
            last_num = 7
        elif pChallenges.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pChallenges.number - 3
            last_num = pChallenges.number + 3
    pChallenges.paginator.pages = range(first_num, last_num + 1)
    pChallenges.count = len(pChallenges)

    content = {
        'challenges': pChallenges,
        'form': form,
        'pageName': 'Label Challenges',
        'pageTitle': 'Label Challenges',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page
    }

    return render(request, 'challenge/label/list.html', content)

@my_login_required
def my_label_challenge_list(request):
    challenges = None
    page = 1
    if request.method == "GET":
        form = LabelChallengeSearchForm(request.GET)
        page = request.GET.get('page')
        if page is None:
            page = 1
        if form.is_valid():
            challenges = LabelChallenge.objects.all().filter(user=request.user)

            name = form.cleaned_data['name']
            label_type = form.cleaned_data['label_type']

            if not name is None:
                challenges = challenges.filter(name__contains=name)
            if not label_type is None and label_type != 0 and label_type != '':
                children_label_type = LabelType.objects.filter(parent_id=label_type)
                if children_label_type.count() > 0:
                    types = []
                    types.append(label_type)
                    for t in children_label_type:
                        types.append(t)
                    challenges = challenges.filter(label_type__in=types)
                else:
                    challenges = challenges.filter(label_type=label_type)

            challenge_type = form.cleaned_data['challenge_type']
            current_time = datetime.now()
            if not challenge_type is None and challenge_type == 'active':
                challenges = challenges.filter(end_time__gte=current_time)
            if not challenge_type is None and challenge_type == 'completed':
                challenges = challenges.filter(end_time__lt=current_time)

    if challenges == None:
        challenges = Challenge.objects.all().filter(user=request.user)
        form = ChallengeSearchForm()

    paginator = Paginator(challenges.order_by('-created_at'), 5)

    try:
        pChallenges = paginator.page(page)
    except PageNotAnInteger:
        pChallenges = paginator.page(1)
    except EmptyPage:
        pChallenges = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pChallenges.number < 4:
            first_num = 1
            last_num = 7
        elif pChallenges.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pChallenges.number - 3
            last_num = pChallenges.number + 3
    pChallenges.paginator.pages = range(first_num, last_num + 1)
    pChallenges.count = len(pChallenges)
    content = {
        'challenges': pChallenges,
        'form': form,
        'pageName': 'My Label Challenges',
        'pageTitle': 'My Label Challenges',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page
    }
    return render(request, 'challenge/label/list.html', content)

def label_challenge_detail(request, unique_id):
    challenge = get_object_or_404(LabelChallenge, unique_id=unique_id)

    if (not request.user.is_authenticated or request.user != challenge.user) and not challenge.is_published:
        messages.success(request, "You can't access this challenge.")
        return redirect('challenge.label_challenge_list')

    form = LabelChallengeSearchForm(request.GET)

    geometry = json.dumps(challenge.geometry)

    page = 1

    if challenge.user == request.user:
        is_mine = True
    else:
        is_mine = False

    challenge_html_detail = render_to_string('challenge/label/modal_detail.html', {'challenge': challenge, 'is_mine': is_mine})

    return render(request, 'challenge/label/challenge_detail.html',
          {
              'challenge': challenge,
              'challenge_html_detail': challenge_html_detail,
              'form': form,
              'geometry': geometry,
              'pageName': 'Label Challenge Detail',
              'pageTitle': challenge.name + ' - Label Challenge',
              'page': page
          })

def label_challenge_leaderboard(request, unique_id):
    challenge = get_object_or_404(LabelChallenge, unique_id=unique_id)

    if (not request.user.is_authenticated or request.user != challenge.user) and not challenge.is_published:
        messages.success(request, "You can't access this challenge.")
        return redirect('challenge.label_challenge_list')

    images = Image.objects.filter(point__intersects=challenge.multipolygon)
    user_json = ImageLabel.objects.filter(image__in=images).values('user').annotate(image_label_count=Count('image')).order_by('-image_label_count').annotate(rank=Window(expression=RowNumber()))

    paginator = Paginator(user_json, 10)
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

    for i in range(len(pItems)):
        user = CustomUser.objects.get(pk=pItems[i]['user'])

        if user is None or not user:
            continue
        pItems[i]['username'] = user.username

        u_images = images.filter(user=user)

        pItems[i]['image_count'] = u_images.count()


    return render(request, 'challenge/label/leaderboard.html',
          {
              'items': pItems,
              'challenge': challenge,
              'pageName': 'Challenge Leaderboard',
              'pageTitle': challenge.name + ' - Challenge Leaderboard',
              'page': page
          })

def ajax_label_challenge_detail(request, unique_id):
    challenge = LabelChallenge.objects.get(unique_id=unique_id)
    if challenge.user == request.user:
        is_mine = True
    else:
        is_mine = False
    serialized_obj = serializers.serialize('json', [challenge, ])
    data = {
        'challenge': json.loads(serialized_obj)
    }

    if not data['challenge']:
        data['error_message'] = "The challenge id doesn't exist."
    else:
        data['challenge_html_detail'] = render_to_string('challenge/label/modal_detail.html', {'challenge': challenge, 'is_mine': is_mine})

    return JsonResponse(data)