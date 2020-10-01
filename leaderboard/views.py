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
from django.db.models import Avg, Count, Min, Sum
from django.db.models.expressions import F, Window
from django.db.models.functions.window import RowNumber
## Custom Libs ##
from lib.functions import *

## Project packages
from accounts.models import CustomUser, MapillaryUser
from tour.models import Tour, TourSequence

## App packages

from .forms import *
from sequence.models import Sequence, ImageViewPoint, CameraMake

############################################################################

MAIN_PAGE_DESCRIPTION = "Leaderboard shows the ranking of users by Monthly and Transport type. One image is counted as 1 point."

############################################################################

def index(request):

    ############
    # update db
    image_vs = ImageViewPoint.objects.filter(owner_id=None)
    print('image_vs: ', image_vs.count())
    if image_vs.count() > 0:
        for image_v in image_vs:
            image_v.owner = image_v.image.sequence.user
            image_v.save()

    ss = Sequence.objects.filter(distance=None)
    if ss.count() > 0:
        for s in ss:
            s.distance = s.getDistance()
            s.save()
    ############


    sequences = None
    page = 1
    form = LeaderboardSearchForm()
    y = None
    m = None
    time_type = None
    if request.method == "GET":
        page = request.GET.get('page')
        if not page or page is None:
            page = 1
        filter_time = request.GET.get('time')
        page = request.GET.get('page')
        transport_type = request.GET.get('transport_type')
        time_type = request.GET.get('time_type')
        camera_makes = request.GET.get('camera_make')

        if time_type is None or not time_type or time_type == 'all_time':
            sequences = Sequence.objects.all().exclude(image_count=0)
        else:
            if time_type == 'monthly':
                if filter_time is None:
                    now = datetime.now()
                    y = now.year
                    m = now.month
                    form.set_timely('YYYY-MM', str(y) + '-' + str(m))
                else:
                    form.set_timely('YYYY-MM', filter_time)
                    y = filter_time.split('-')[0]
                    m = filter_time.split('-')[1]
                sequences = Sequence.objects.filter(
                    captured_at__month=m,
                    captured_at__year=y
                ).exclude(image_count=0)
                time_type = 'monthly'
            elif time_type == 'yearly':
                if filter_time is None:
                    now = datetime.now()
                    y = now.year
                    form.set_timely('YYYY', str(y))
                else:
                    form.set_timely('YYYY', filter_time)
                    y = filter_time
                sequences = Sequence.objects.filter(
                    captured_at__year=y
                ).exclude(image_count=0)
                time_type = 'yearly'

        if not transport_type is None and transport_type != 0 and transport_type != '':
            children_trans_type = TransType.objects.filter(parent_id=transport_type)
            if children_trans_type.count() > 0:
                types = []
                types.append(transport_type)
                for t in children_trans_type:
                    types.append(t.pk)
                sequences = sequences.filter(transport_type_id__in=types)
            else:
                sequences = sequences.filter(transport_type_id=transport_type)

            form.set_transport_type(transport_type)

        if not camera_makes is None and len(camera_makes) > 0:
            sequences = sequences.filter(camera_make__in=camera_makes)
            form.set_camera_makes(camera_makes)

    if sequences == None:

        sequences = Sequence.objects.all().exclude(image_count=0)

    filter_type = request.GET.get('filter_type')

    top_title = 'Uploads Leaderboard'
    if not filter_type is None and filter_type == '1':
        user_json = sequences.values('user').annotate(all_distance=Sum('distance')).order_by('-all_distance')
        form.set_filter_type(filter_type)
        top_title = 'Distance Leaderboard'

    elif not filter_type is None and filter_type == '2':
        user_json = ImageViewPoint.objects.filter(image__sequence__in=sequences).values('owner').annotate(
            image_view_count=Count('image')).order_by('-image_view_count')
        form.set_filter_type(filter_type)
        top_title = 'View Points Leaderboard'

    else:
        user_json = sequences.values('user').annotate(image_count=Sum('image_count')).order_by('-image_count')

    paginator = Paginator(user_json, 10)

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
        pItems[i]['rank'] = i + 1
        if 'owner' in pItems[i].keys():
            pItems[i]['user'] = pItems[i]['owner']
        user = CustomUser.objects.get(pk=pItems[i]['user'])

        if user is None or not user:
            continue
        pItems[i]['username'] = user.username

        u_sequences = sequences.filter(user=user)

        used_cameras = []
        u_camera_sequences = u_sequences.values('camera_make').annotate(camera_count=Count('camera_make'))
        if u_camera_sequences.count() > 0:
            for u_s in u_camera_sequences:
                if u_s['camera_make'] is None:
                    continue
                camera = CameraMake.objects.get(pk=u_s['camera_make'])
                used_cameras.append(camera.name)

        used_cameras_str = ', '.join(used_cameras)
        pItems[i]['used_cameras_str'] = used_cameras_str

        used_trans = []
        u_trans_sequences = u_sequences.values('transport_type').annotate(camera_count=Count('transport_type'))
        if u_trans_sequences.count() > 0:
            for u_s in u_trans_sequences:
                transport_t = TransType.objects.filter(pk=u_s['transport_type'])
                if transport_t.count() == 0:
                    continue
                used_trans.append(transport_t[0].name)
        used_trans.sort()
        used_trans_str = ', '.join(used_trans)
        pItems[i]['transport_type'] = used_trans_str

        u_distance = 0
        u_photo_count = 0
        if u_sequences.count() > 0:
            for u_s in u_sequences:
                u_distance += float(u_s.getDistance())
                u_photo_count += u_s.getImageCount()
        pItems[i]['distance'] = "%.3f" % u_distance
        pItems[i]['photo_count'] = u_photo_count

        u_viewpoints = ImageViewPoint.objects.filter(image__sequence__in=sequences, owner=user)
        u_view_point = u_viewpoints.count()
        pItems[i]['view_points'] = u_view_point


    if time_type is None:
        time_type = 'all_time'
    form.set_time_type(time_type)
    content = {
        'items': pItems,
        'form': form,
        'pageName': 'Leaderboard',
        'pageTitle': 'Leaderboard',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page,
        'time_type': time_type,
        'top_title': top_title,
        'filter_time': filter_time
    }
    return render(request, 'leaderboard/list.html', content)
