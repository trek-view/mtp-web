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
from sequence.models import Sequence
from django.db.models.expressions import F, Window
from django.db.models.functions.window import RowNumber
from django.db.models import Avg, Count, Min, Sum
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
    return redirect('challenge.challenge_list', page=1)

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

            transport_type = form.cleaned_data['transport_type']
            if not transport_type is None:
                challenge.transport_type.add(transport_type)

            messages.success(request, 'A challenge was created successfully.')

            return redirect('challenge.my_challenge_list')
    else:
        form = ChallengeForm()
    content = {
        'form': form,
        'pageName': 'Create Challenge',
        'pageTitle': 'Create Challenge'
    }
    return render(request, 'challenge/create.html', content)

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
            if not transport_type is None:
                challenge.transport_type.add(transport_type)
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
    return render(request, 'challenge/edit.html', content)

@my_login_required
def my_challenge_delete(request, unique_id):
    challenge = get_object_or_404(Challenge, unique_id=unique_id)
    if challenge.user == request.user:
        challenge.delete()
        messages.success(request, 'Challenge "%s" is deleted successfully.' % challenge.name)
    else:
        messages.error(request, "This user hasn't permission")

    return redirect('challenge.index')

def challenge_list(request, page):
    challenges = None
    if request.method == "GET":
        form = ChallengeSearchForm(request.GET)

        if form.is_valid():
            challenges = Challenge.objects.all().filter(is_published=True)

            name = form.cleaned_data['name']
            transport_type = form.cleaned_data['transport_type']
            expected_count_min = form.cleaned_data['expected_count_min']
            expected_count_max = form.cleaned_data['expected_count_max']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            if not name is None:
                challenges = challenges.filter(name__contains=name)
            print(transport_type)
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

            if not expected_count_min is None:
                challenges = challenges.filter(expected_count__gte=expected_count_min)
            if not expected_count_max is None:
                challenges = challenges.filter(expected_count__lte=expected_count_max)
            if not start_time is None:
                challenges = challenges.filter(end_time__gte=start_time)
            if not end_time is None:
                challenges = challenges.filter(start_time__lte=end_time)

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
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }

    return render(request, 'challenge/list.html', content)

def challenge_detail(request, unique_id):
    challenge = get_object_or_404(Challenge, unique_id=unique_id)

    if (not request.user.is_authenticated or request.user != challenge.user) and not challenge.is_published:
        messages.success(request, "You can't access this challenge.")
        return redirect('challenge.challenge_list')

    form = ChallengeSearchForm(request.GET)

    geometry = json.dumps(challenge.geometry)

    if challenge.user == request.user:
        is_mine = True
    else:
        is_mine = False

    challenge_html_detail = render_to_string('challenge/modal_detail.html', {'challenge': challenge, 'is_mine': is_mine})

    return render(request, 'challenge/challenge_detail.html',
          {
              'challenge': challenge,
              'challenge_html_detail': challenge_html_detail,
              'form': form,
              'geometry': geometry,
              'pageName': 'Challenge Detail',
              'pageTitle': challenge.name + ' - Challenge'
          })

def challenge_leaderboard(request, unique_id):
    challenge = get_object_or_404(Challenge, unique_id=unique_id)

    if (not request.user.is_authenticated or request.user != challenge.user) and not challenge.is_published:
        messages.success(request, "You can't access this challenge.")
        return redirect('challenge.challenge_list')
    print(challenge.multipolygon.coords)
    sequences = Sequence.objects.filter(is_published=True, geometry_coordinates__crosses=challenge.multipolygon)
    print(sequences)

    user_json = sequences.values('user').annotate(image_count=Sum('image_count')).order_by('-image_count').annotate(rank=Window(expression=RowNumber()))

    print(user_json)
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
    form = ChallengeSearchForm(request.GET)

    for i in range(len(pItems)):
        user = CustomUser.objects.get(pk=pItems[i]['user'])

        if user is None or not user:
            continue
        pItems[i]['username'] = user.username


    return render(request, 'challenge/leaderboard.html',
          {
              'items': pItems,
              'challenge': challenge,
              'form': form,
              'pageName': 'Challenge Leaderboard',
              'pageTitle': challenge.name + ' - Challenge Leaderboard'
          })

@my_login_required
def my_challenge_list(request, page):
    challenges = None
    if request.method == "GET":
        form = ChallengeSearchForm(request.GET)

        if form.is_valid():
            challenges = Challenge.objects.all().filter(user=request.user)

    if challenges == None:
        challenges = Challenge.objects.all().filter(user=request.user)
        form = ChallengeSearchForm()

    paginator = Paginator(challenges.order_by('-created_at'), 10)

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
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }
    return render(request, 'challenge/list.html', content)

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
        data['challenge_html_detail'] = render_to_string('challenge/modal_detail.html', {'challenge': challenge, 'is_mine': is_mine})

    return JsonResponse(data)