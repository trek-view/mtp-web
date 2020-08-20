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
from django.contrib.gis.geos import Point

## Custom Libs ##
from lib.functions import *

## Project packages
from accounts.models import CustomUser

## App packages

# That includes from .models import *
from .forms import * 

############################################################################

def home(request):
    return redirect('guidebook.guidebook_list', page=1)

def guidebook_list(request, page):
    guidebooks = None
    if request.method == "GET":
        form = GuidebookSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            category = form.cleaned_data['category']
            tags = form.cleaned_data['tag']
            guidebooks = Guidebook.objects.all().filter(
                is_published=True,
                is_approved=True
            )
            if name:
                guidebooks = guidebooks.filter(name__contains=name)
            if category:
                guidebooks = guidebooks.filter(category_id=category)

            if len(tags) > 0:
                guidebooks = guidebooks.filter(tag__overlap=tags)

    if guidebooks == None:
        guidebooks = Guidebook.objects.all().filter(is_published=True, is_approved=True)
        form = GuidebookSearchForm()

    paginator = Paginator(guidebooks.order_by('-created_at'), 5)

    try:
        pGuidebooks = paginator.page(page)
    except PageNotAnInteger:
        pGuidebooks = paginator.page(1)
    except EmptyPage:
        pGuidebooks = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pGuidebooks.number < 4:
            first_num = 1
            last_num = 7
        elif pGuidebooks.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pGuidebooks.number - 3
            last_num = pGuidebooks.number + 3
    pGuidebooks.paginator.pages = range(first_num, last_num + 1)
    pGuidebooks.count = len(pGuidebooks)
    return render(request, 'guidebook/guidebook_list.html', {'guidebooks': pGuidebooks, 'form': form, 'pageName': 'guidebook-list'})

@my_login_required
def my_guidebook_list(request, page):
    guidebooks = None
    if request.method == "GET":
        form = GuidebookSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            category = form.cleaned_data['category']
            tags = form.cleaned_data['tag']
            guidebooks = Guidebook.objects.all().filter(
                user=request.user
            )
            if name:
                guidebooks = guidebooks.filter(name__contains=name)
            if category:
                guidebooks = guidebooks.filter(category_id=category)

            if len(tags) > 0:
                guidebooks = guidebooks.filter(tag__overlap=tags)

    if guidebooks == None:
        guidebooks = Guidebook.objects.all().filter(
            user=request.user
        )
        form = GuidebookSearchForm()

    paginator = Paginator(guidebooks.order_by('-created_at'), 5)

    try:
        pGuidebooks = paginator.page(page)
    except PageNotAnInteger:
        pGuidebooks = paginator.page(1)
    except EmptyPage:
        pGuidebooks = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pGuidebooks.number < 4:
            first_num = 1
            last_num = 7
        elif pGuidebooks.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pGuidebooks.number - 3
            last_num = pGuidebooks.number + 3
    pGuidebooks.paginator.pages = range(first_num, last_num + 1)
    pGuidebooks.count = len(pGuidebooks)
    return render(request, 'guidebook/guidebook_list.html', {'guidebooks': pGuidebooks, 'form': form, 'pageName': 'my-guidebook-list'})

def guidebook_detail(request, unique_id):
    guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
    if request.user.is_authenticated:
        guidebook_like = GuidebookLike.objects.filter(guidebook=guidebook, user=request.user)
        if guidebook_like and guidebook_like.count() > 0:
            is_liked = True
        else:
            is_liked = False
    else:
        is_liked = False
    form = SceneForm()
    poi_form = PointOfInterestForm()
    return render(request, 'guidebook/guidebook_detail.html', {'guidebook': guidebook, 'is_liked': is_liked, 'form': form, 'poi_form': poi_form, 'pageName': 'guidebook-detail'})

@my_login_required
def guidebook_create(request, unique_id=None):
    if request.method == "POST":
        form = GuidebookForm(request.POST, request.FILES)

        if form.is_valid():
            if unique_id is None:
                guidebook = form.save(commit=False)
                guidebook.user = request.user
                guidebook.save()
                try:
                    # send email to creator
                    subject = 'Your guidebook post is under review'
                    html_message = render_to_string(
                        'emails/guidebook/guidebook/create.html',
                        {'subject': subject, 'guidebook': guidebook},
                        request
                    )
                    send_mail_with_html(subject, html_message, request.user.email)
                    # send email to admin
                    staffs = CustomUser.objects.filter(is_staff=True, is_active=True)
                    staff_emails = []
                    for staff in staffs:
                        staff_emails.append(staff.email)
                    if len(staff_emails) > 0:
                        subject = 'Guidebook post needs to be approved'
                        html_message = render_to_string(
                            'emails/guidebook/guidebook/create_admin.html',
                            {'subject': subject, 'guidebook': guidebook},
                            request
                        )
                        send_mail_with_html(subject, html_message, staff_emails)
                except:
                    print('email sending error!')
            else:
                guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
                guidebook.name = form.cleaned_data['name']
                guidebook.description = form.cleaned_data['description']
                guidebook.cover_image = form.cleaned_data['cover_image']
                guidebook.category = form.cleaned_data['category']
                guidebook.tag = form.cleaned_data['tag']
                guidebook.save()



            messages.success(request, 'A guidebook was created successfully.')
            return redirect('guidebook.add_scene', unique_id=guidebook.unique_id)
    else:
        if unique_id:
            guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
            form = GuidebookForm(instance=guidebook)
        else:
            form = GuidebookForm()
    return render(request, 'guidebook/create_main.html', {'form': form, 'pageName': 'guidebook-create'})

@my_login_required
def ajax_guidebook_update(request, unique_id = None):
    if request.method == "POST":
        form = GuidebookForm(request.POST)

        if form.is_valid():
            guidebook = Guidebook.objects.get(unique_id=unique_id)
            if not guidebook:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The Guidebook does not exist or has no access.'
                })

            guidebook.name = form.cleaned_data['name']
            guidebook.description = form.cleaned_data['description']
            guidebook.category = form.cleaned_data['category']
            guidebook.tag = form.cleaned_data['tag']
            guidebook.save()
            print('========')
            print(guidebook.getTagStr)
            return JsonResponse({
                'status': 'success',
                'message': 'Guidebook was uploaded successfully.',
                'guidebook': {
                    'title': guidebook.name,
                    'description': guidebook.description,
                    'category': guidebook.category.name,
                    'tag': guidebook.getTags()
                }
            })

    return JsonResponse({
        'status': 'failed',
        'message': 'The Guidebook does not exist or has no access.'
    })

@my_login_required
def add_scene(request, unique_id):
    guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
    if guidebook.user != request.user:
        messages.error(request, "You can't access the page.")
        return redirect('/')
    form = SceneForm()
    poi_form = PointOfInterestForm()
    g_form = GuidebookForm(instance=guidebook)
    return render(request, 'guidebook/add_scene.html', {'guidebook': guidebook, 'g_form': g_form, 'form': form, 'poi_form': poi_form, 'pageName': 'add-scene'})

@my_login_required
def ajax_upload_file(request, unique_id):
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist or has no access.'
        })

    if request.method == "POST":
        form = GuidebookImageForm(request.POST, request.FILES)
        if form.is_valid():
            new_guidebook = form.save(commit=False)
            guidebook.cover_image = new_guidebook.cover_image
            guidebook.save()
            return JsonResponse({
                'status': 'success',
                'message': 'A cover image is uploaded successfully.'
            })

@my_login_required
def ajax_add_scene(request, unique_id):
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist or has no access.'
        })

    if request.method == "POST":
        form = SceneForm(request.POST)
        if form.is_valid():
            image_key = form.cleaned_data['image_key']
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            scene = Scene.objects.filter(image_key=image_key, guidebook=guidebook)
            lat = float(form.cleaned_data['lat'])
            lng = float(form.cleaned_data['lng'])

            if scene:
                old_scene = scene[0]
                old_scene.title = title
                old_scene.description = description
                old_scene.lat = lat
                old_scene.lng = lng
                old_scene.save()
                return JsonResponse({
                    'type': 'update',
                    'scene_id': old_scene.pk,
                    'title': old_scene.title,
                    'description': old_scene.description,
                    'status': 'success',
                    'message': 'Scene is updated successfully.'
                })
            else:
                new_scene = Scene()
                new_scene.guidebook = guidebook
                new_scene.image_key = image_key
                new_scene.title = title
                new_scene.description = description
                new_scene.lat = lat
                new_scene.lng = lng
                scenes = guidebook.getScenes()
                max_sort = 0
                for s in scenes:
                    if s.sort > max_sort:
                        max_sort = s.sort
                new_scene.sort = max_sort + 1
                new_scene.save()
                scene_box_html = render_to_string(
                    'guidebook/scene_edit_box.html',
                    {'guidebook': guidebook, 'scene': new_scene},
                    request
                )
                scenes = Scene.objects.filter(guidebook=guidebook)
                if scenes and scenes.count() > 0:
                    scene_count = scenes.count()
                else:
                    scene_count = 0
                return JsonResponse({
                    'type': 'new',
                    'scene_id': new_scene.pk,
                    'scene_box_html': scene_box_html,
                    'scene_count': scene_count,
                    'status': 'success',
                    'message': 'A new Scene is added successfully.'
                })
    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to save Scene!'
    })

@my_login_required
def ajax_order_scene(request, unique_id):
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist or has no access.'
        })

    if request.method == "POST":
        order_str = request.POST.get('order_list')
        order_list = order_str.split(',')
        scene_list = []
        for i in range(len(order_list)):
            print(str(i) + ': ' + order_list[i])
            scene = Scene.objects.get(pk=int(order_list[i]))
            if scene is None or scene.guidebook != guidebook:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The Scene does not exist or has no access.'
                })
            scene_list.append(scene)
        for i in range(len(order_list)):
            scene_list[i].sort = i
            scene_list[i].save()

        return JsonResponse({
            'status': 'success',
            'message': 'Scenes are ordered successfully.'
        })

    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to save Scene!'
    })

@my_login_required
def ajax_save_poi(request, unique_id, pk):
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist or has no access.'
        })
    scene = Scene.objects.get(pk=pk)
    if not scene or scene.guidebook.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Scene does not exist or has no access.'
        })
    if request.method == "POST":
        if request.POST.get('type') == 'new':
            poi = PointOfInterest()
            poi.title = 'Undefined Title'
            poi.description = ''
            poi.category_id = 1
            poi.position_x = request.POST.get('position_x')
            poi.position_y = request.POST.get('position_y')
            poi.scene = scene
            poi.save()
            message = 'A new Point of Interest is created successfully.'

        elif request.POST.get('type') == 'move':
            poi = PointOfInterest.objects.get(pk=request.POST.get('poi_id'))
            if not poi:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The Point of Interest does not exist or has no access.'
                })
            poi.position_x = request.POST.get('position_x')
            poi.position_y = request.POST.get('position_y')
            poi.save()
            message = 'Position is updated successfully.'
        else:
            poi = PointOfInterest.objects.get(pk=request.POST.get('poi_id'))
            if not poi:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The Point of Interest does not exist or has no access.'
                })
            if request.POST.get('title') == '':
                return JsonResponse({
                    'status': 'failed',
                    'message': 'Title is required!'
                })
            poi.title = request.POST.get('title')
            poi.category_id = request.POST.get('category_id')
            poi.description = request.POST.get('description')
            poi.save()
            message = 'Point of Interest is saved successfully.'

        serialized_obj = serializers.serialize('json', [poi, ])
        json_poi = json.loads(serialized_obj)
        poi_form = PointOfInterestForm(instance=poi)
        poi_box_html = render_to_string(
            'guidebook/poi_edit_box.html',
            {'poi': poi, 'poi_form': poi_form},
            request
        )
        return JsonResponse({
            'status': 'success',
            'poi': json_poi,
            'poi_box_html': poi_box_html,
            'message': message
        })

    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to save Point of Interest!'
    })

@my_login_required
def ajax_delete_poi(request, unique_id, pk):
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist or has no access.'
        })
    scene = Scene.objects.get(pk=pk)
    if not scene or scene.guidebook.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Scene does not exist or has no access.'
        })
    if request.method == "POST":
        poi = PointOfInterest.objects.get(pk=request.POST.get('poi_id'))
        if not poi:
            return JsonResponse({
                'status': 'failed',
                'message': 'The Point of Interest does not exist or has no access.'
            })
        poi.delete()
        message = 'Point of Interest is deleted successfully.'

        return JsonResponse({
            'status': 'success',
            'message': message
        })

    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to delete Point of Interest!'
    })

def ajax_get_scene(request, unique_id):
    image_key = request.GET['image_key']
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist or has no access.'
        })

    scene = Scene.objects.filter(guidebook=guidebook, image_key=image_key)
    if not scene or scene.count() == 0:
        return JsonResponse({
            'status': 'failed',
            'message': 'The scene does not exist or has no access.'
        })
    else:
        pois = PointOfInterest.objects.filter(scene=scene[0])
        poi_list = []
        for poi in pois:
            poi_box_html = render_to_string(
                'guidebook/poi_box.html',
                {'poi': poi},
                request
            )
            poi_json = serializers.serialize('json', [poi, ])
            json_poi = json.loads(poi_json)
            poi_list.append({
                'poi': json_poi,
                'poi_box_html': poi_box_html
            })

        scene_first = scene[0]
        scene_first.poi_list = poi_list

        scene_json = serializers.serialize('json', [scene_first, ])
        json_scene = json.loads(scene_json)

        return JsonResponse({
            'status': 'success',
            'scene': json_scene,
            'poi_list': poi_list
        })

@my_login_required
def ajax_get_edit_scene(request, unique_id):
    image_key = request.GET['image_key']
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist or has no access.'
        })

    scene = Scene.objects.filter(guidebook=guidebook, image_key=image_key)
    if not scene or scene.count() == 0:
        return JsonResponse({
            'status': 'failed',
            'message': 'The scene does not exist or has no access.'
        })
    else:
        pois = PointOfInterest.objects.filter(scene=scene[0])
        poi_list = []
        for poi in pois:
            poi_form = PointOfInterestForm(instance=poi)
            poi_box_html = render_to_string(
                'guidebook/poi_edit_box.html',
                {'poi': poi, 'poi_form': poi_form},
                request
            )
            poi_json = serializers.serialize('json', [poi, ])
            json_poi = json.loads(poi_json)
            poi_list.append({
                'poi': json_poi,
                'poi_box_html': poi_box_html
            })

        scene_first = scene[0]
        scene_first.poi_list = poi_list

        scene_json = serializers.serialize('json', [scene_first, ])
        json_scene = json.loads(scene_json)

        return JsonResponse({
            'status': 'success',
            'scene': json_scene,
            'poi_list': poi_list
        })

@my_login_required
def ajax_get_scene_list(request, unique_id):
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist or has no access.'
        })

    scenes = Scene.objects.filter(guidebook=guidebook)
    scenes_json = []
    for scene in scenes:
        scene_json = serializers.serialize('json', [scene, ])
        json_scene = json.loads(scene_json)
        scenes_json.append(json_scene)

    return JsonResponse({
        'status': 'success',
        'scene_list': scenes_json
    })

@my_login_required
def ajax_delete_scene(request, unique_id, pk):
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist or has no access.'
        })

    if request.method == "POST":
        scene = Scene.objects.get(pk=pk)
        if not scene or scene.guidebook.user != request.user:
            return JsonResponse({
                'status': 'failed',
                'message': 'The Scene does not exist or has no access.'
            })
        pois = PointOfInterest.objects.filter(scene=scene)
        if pois and pois.count() > 0:
            for p in pois:
                p.delete()
        if scene.image_url:
            os.remove("media/" + scene.image_url)
        scene.delete()


        message = 'Scene is deleted successfully.'

        scenes = Scene.objects.filter(guidebook=guidebook)
        if scenes and scenes.count() > 0:
            scene_count = scenes.count()
        else:
            scene_count = 0
            guidebook.is_published = False
            guidebook.save()
        return JsonResponse({
            'status': 'success',
            'message': message,
            'scene_count': scene_count
        })

    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to delete Scene!'
    })

@my_login_required
def check_like(request, unique_id):
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist.'
        })

    if guidebook.user == request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'This guidebook is created by you.'
        })

    guidebook_like = GuidebookLike.objects.filter(guidebook=guidebook, user=request.user)
    if guidebook_like:
        for g in guidebook_like:
            g.delete()
        liked_guidebook = GuidebookLike.objects.filter(guidebook=guidebook)
        if not liked_guidebook:
            liked_count = 0
        else:
            liked_count = liked_guidebook.count()
        return JsonResponse({
            'status': 'success',
            'message': 'Unliked',
            'is_checked': False,
            'liked_count': liked_count
        })
    else:
        guidebook_like = GuidebookLike()
        guidebook_like.guidebook = guidebook
        guidebook_like.user = request.user
        guidebook_like.save()
        liked_guidebook = GuidebookLike.objects.filter(guidebook=guidebook)
        if not liked_guidebook:
            liked_count = 0
        else:
            liked_count = liked_guidebook.count()
        return JsonResponse({
            'status': 'success',
            'message': 'Liked',
            'is_checked': True,
            'liked_count': liked_count
        })

@my_login_required
def check_publish(request, unique_id):
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist.'
        })

    if guidebook.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'This guidebook is not created by you.'
        })

    if not guidebook.is_approved:
        return JsonResponse({
            'status': 'failed',
            'message': "This guidebook isn't approved."
        })

    if guidebook.is_published:
        guidebook.is_published = False
        message = 'Unpublished'
    else:
        guidebook.is_published = True
        message = 'Published'
    guidebook.save()
    return JsonResponse({
        'status': 'success',
        'message': message,
        'is_published': guidebook.is_published
    })

@my_login_required
def guidebook_delete(request, unique_id):
    guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
    if guidebook.user == request.user:
        guidebook_like = GuidebookLike.objects.filter(guidebook=guidebook)
        if guidebook_like:
            for g in guidebook_like:
                g.delete()

        scenes = Scene.objects.filter(guidebook=guidebook)
        if scenes:
            for s in scenes:
                pois = PointOfInterest.objects.filter(scene=s)
                if pois:
                    for p in pois:
                        p.delete()

        guidebook.delete()
        messages.success(request, 'Photographer "%s" is deleted successfully.' % guidebook.name)
    else:
        messages.error(request, "This user hasn't permission")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))