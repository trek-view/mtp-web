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
PHOTOGRAPHER_PAGE_DESCRIPTION = ""


############################################################################

def index(request):
    return redirect('photographer.photographer_list')

@my_login_required
def photographer_create(request):
    photographer = Photographer.objects.filter()
    if request.method == "POST":
        form = PhotographerForm(request.POST)

        if form.is_valid():
            photographer = form.save(commit=False)
            photographer.user = request.user
            geometry = json.loads(photographer.geometry)
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
            photographer.multipolygon = multipoly

            for geo in geometry:
                geo['properties']['photographer_id'] = str(photographer.unique_id)
            photographer.geometry = json.dumps(geometry)

            photographer.save()

            capture_types = form.cleaned_data['capture_type']
            capture_method = form.cleaned_data['capture_method']
            if not capture_types is None:
                photographer.capture_type.clear()
                for capture_type in capture_types:
                    photographer.capture_type.add(capture_type)
            if not capture_method is None:
                photographer.capture_method.clear()
                for capture_m in capture_method:
                    photographer.capture_method.add(capture_m)

            messages.success(request, 'A photographer was created successfully.')

            return redirect('photographer.my_photographer_list')
    else:
        form = PhotographerForm()
    content = {
        'form': form,
        'pageName': 'Create Photographer',
        'pageTitle': 'Create Photographer'
    }
    return render(request, 'photographer/create.html', content)

@my_login_required
def photographer_hire(request, unique_id):
    photographer = get_object_or_404(Photographer, unique_id=unique_id)
    if request.method == "POST":
        form = PhotographerEnquireForm(request.POST)
        if form.is_valid():
            photographerEnquire = form.save(commit=False)
            photographerEnquire.photographer = photographer
            photographerEnquire.user = request.user
            photographerEnquire.email = request.user.email
            photographerEnquire.save()

            try:
                # send email to applicant
                subject = 'Your message has been sent'
                html_message = render_to_string(
                    'emails/photographer/enquire_applicant.html',
                    {'subject': subject, 'photographer': photographer, 'photographer_enquire': photographerEnquire},
                    request
                )

                send_mail_with_html(subject, html_message, request.user.email, photographer.user.email)

            except:
                print('email 1 sending error!')
            try:
                # send email to photographer creator
                subject = photographerEnquire.subject
                html_message = render_to_string(
                    'emails/photographer/enquire_creator.html',
                    {'subject': subject, 'photographer': photographer, 'photographer_enquire': photographerEnquire},
                    request
                )
                send_mail_with_html(subject, html_message, photographer.user.email, request.user.email)
            except:
                print('email 2 sending error!')

            messages.success(request, 'You have succeeded in hiring photographers.')

            return redirect('photographer.photographer_list')
    else:
        form = PhotographerEnquireForm()
    content = {
        'form': form,
        'photographer': photographer,
        'pageName': 'Hire Photographer',
        'PageTitle': photographer.name + ' - Hire Photographer'
    }
    return render(request, 'photographer/hire.html', content)

@my_login_required
def photographer_edit(request, unique_id):
    photographer = get_object_or_404(Photographer, unique_id=unique_id)
    if request.method == "POST":
        form = PhotographerForm(request.POST, instance=photographer)
        if form.is_valid():
            photographer = form.save(commit=False)
            photographer.user = request.user
            photographer.updated_at = datetime.now()
            photographer.save()
            geometry = json.loads(photographer.geometry)

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
            photographer.multipolygon = multipoly

            for geo in geometry:
                geo['properties']['photographer_id'] = str(photographer.unique_id)
            photographer.geometry = json.dumps(geometry)
            photographer.save()

            capture_types = form.cleaned_data['capture_type']
            capture_method = form.cleaned_data['capture_method']
            if not capture_types is None:
                photographer.capture_type.clear()
                for capture_type in capture_types:
                    photographer.capture_type.add(capture_type)
            if not capture_method is None:
                photographer.capture_method.clear()
                for capture_m in capture_method:
                    photographer.capture_method.add(capture_m)

            messages.success(request, 'Photographer "%s" is updated successfully.' % photographer.name)
            return redirect('photographer.index')
    else:
        form = PhotographerForm(instance=photographer)
    content = {
        'form': form,
        'pageName': 'Edit Photographer',
        'photographer': photographer,
        'pageTitle': photographer.name + ' - Edit Photographer'
    }
    return render(request, 'photographer/edit.html', content)

@my_login_required
def my_photographer_delete(request, unique_id):
    photographer = get_object_or_404(Photographer, unique_id=unique_id)
    if photographer.user == request.user:
        photographer.delete()
        messages.success(request, 'Photographer "%s" is deleted successfully.' % photographer.name)
    else:
        messages.error(request, "This user hasn't permission")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def photographer_list(request):
    photographers = None
    page = 1
    if request.method == "GET":
        form = PhotographerSearchForm(request.GET)
        page = request.GET.get('page')
        if page is None:
            page = 1
        if form.is_valid():

            capture_types = form.cleaned_data['capture_type']
            capture_method = form.cleaned_data['capture_method']
            image_quality = form.cleaned_data['image_quality']
            print(image_quality)

            photographers = Photographer.objects.all().filter(is_published=True)

            if not image_quality is None:
                photographers = photographers.filter(image_quality=image_quality)

            if not capture_types is None and len(capture_types) > 0:
                ps = Photographer.objects.filter(capture_type__in=capture_types)
                photographers = photographers.filter(pk__in=ps)

            if not capture_method is None and len(capture_method) > 0:
                ps = Photographer.objects.filter(capture_method__in=capture_method)
                photographers = photographers.filter(pk__in=ps)

    if photographers == None:
        photographers = Photographer.objects.all().filter(is_published=True)
        form = PhotographerSearchForm()

    paginator = Paginator(photographers.order_by('-created_at'), 5)

    try:
        pPhotographers = paginator.page(page)
    except PageNotAnInteger:
        pPhotographers = paginator.page(1)
    except EmptyPage:
        pPhotographers = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pPhotographers.number < 4:
            first_num = 1
            last_num = 7
        elif pPhotographers.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pPhotographers.number - 3
            last_num = pPhotographers.number + 3
    pPhotographers.paginator.pages = range(first_num, last_num + 1)
    pPhotographers.count = len(pPhotographers)

    photographers = Photographer.objects.filter(user=request.user)
    photographer = None
    if photographers.count() > 0:
        photographer = photographers[0]

    content = {
        'photographers': pPhotographers,
        'form': form,
        'pageName': 'Photographers',
        'pageTitle': 'Photographers',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page,
        'photographer': photographer
    }

    return render(request, 'photographer/list.html', content)

def photographer_detail(request, unique_id):
    photographer = get_object_or_404(Photographer, unique_id=unique_id)

    if (not request.user.is_authenticated or request.user != photographer.user) and not photographer.is_published:
        messages.success(request, "You can't access this photographer.")
        return redirect('photographer.photographer_list')

    form = PhotographerSearchForm()

    geometry = json.dumps(photographer.geometry)

    if photographer.user == request.user:
        is_mine = True
    else:
        is_mine = False

    photographer.options = photographer.getCaptureType() + ', ' + photographer.getCaptureMethod()
    hire_url = reverse('photographer.photographer_hire', kwargs={'unique_id': str(photographer.unique_id)})
    photographer_html_detail = render_to_string('photographer/modal_detail.html',
                                                {'photographer': photographer, 'hire_url': hire_url,
                                                 'is_mine': is_mine})

    return render(request, 'photographer/photographer_detail.html',
      {
          'photographer': photographer,
          'photographer_html_detail': photographer_html_detail,
          'form': form,
          'geometry': geometry,
          'pageName': 'Photographer Detail',
          'pageTitle': photographer.name + ' - Photographer',
          'page': 1
      })

@my_login_required
def my_photographer_list(request):
    photographers = None
    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        form = PhotographerSearchForm(request.GET)
        if form.is_valid():
            capture_type = form.cleaned_data['capture_type']
            capture_method = form.cleaned_data['capture_method']
            photographers = Photographer.objects.all().filter(user=request.user)
            if len(capture_type) > 0:
                photographers = photographers.filter(capture_type__in=capture_type)
            if len(capture_method) > 0:
                photographers = photographers.filter(capture_method__in=capture_method)

    if photographers == None:
        photographers = Photographer.objects.all().filter(user=request.user)
        form = PhotographerSearchForm()

    paginator = Paginator(photographers.order_by('-created_at'), 5)

    try:
        pPhotographers = paginator.page(page)
    except PageNotAnInteger:
        pPhotographers = paginator.page(1)
    except EmptyPage:
        pPhotographers = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pPhotographers.number < 4:
            first_num = 1
            last_num = 7
        elif pPhotographers.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pPhotographers.number - 3
            last_num = pPhotographers.number + 3
    pPhotographers.paginator.pages = range(first_num, last_num + 1)
    pPhotographers.count = len(pPhotographers)
    content = {
        'photographers': pPhotographers,
        'form': form,
        'pageName': 'My Photographers',
        'pageTitle': 'My Photographers',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page
    }
    return render(request, 'photographer/list.html', content)

def ajax_photographer_detail(request, unique_id):
    photographer = Photographer.objects.get(unique_id=unique_id)
    if photographer.user == request.user:
        is_mine = True

    else:
        is_mine = False
    serialized_obj = serializers.serialize('json', [photographer, ])
    data = {
        'photographer': json.loads(serialized_obj)
    }

    if not data['photographer']:
        data['error_message'] = "The photographer id doesn't exist."
    else:
        photographer.options = photographer.getCaptureType() + ', ' + photographer.getCaptureMethod()
        hire_url = reverse('photographer.photographer_hire', kwargs={'unique_id': str(photographer.unique_id)})
        data['photographer_html_detail'] = render_to_string('photographer/modal_detail.html',
                                                            {'photographer': photographer, 'hire_url': hire_url,
                                                             'is_mine': is_mine})

    return JsonResponse(data)