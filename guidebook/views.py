# Python packages
import json
import os

from django.contrib import messages
from django.contrib.gis.geos import Point
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import (
    JsonResponse, )
# Django Packages
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse

# Project packages
from accounts.models import CustomUser
# Custom Libs
from lib.functions import *
from lib.django_db_functions import get_correct_sql
# That includes from .models import *
from .forms import *

# App packages

############################################################################

MAIN_PAGE_DESCRIPTION = """Create a guidebook of street-level photos to show people around a location. View others people have created to help plan your next adventure."""

############################################################################


def home(request):
    return redirect('guidebook.guidebook_list')


# noinspection DuplicatedCode
def guidebook_list(request):
    scenes = Scene.objects.filter()
    for scene in scenes:
        scene.point = Point([scene.lng, scene.lat])
        scene.save()
    guidebooks = None
    page = 1
    order_type = 'latest_at'
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        order_type = request.GET.get('order_type')
        form = GuidebookSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            category = form.cleaned_data['category']
            tags = form.cleaned_data['tag']
            username = form.cleaned_data['username']
            image_key = form.cleaned_data['image_key']
            like = form.cleaned_data['like']
            guidebooks = Guidebook.objects.all().filter(
                is_published=True,
                is_approved=True
            )
            if name is not None and name != '':
                guidebooks = guidebooks.filter(name__icontains=name)
            if category is not None and category != '':
                guidebooks = guidebooks.filter(category__name=category)
            if username and username != '':
                users = CustomUser.objects.filter(username__icontains=username)
                guidebooks = guidebooks.filter(user__in=users)
            if len(tags) > 0:
                for tag in tags:
                    guidebooks = guidebooks.filter(tag=tag)
            if like and like != 'all':
                guidebook_likes = GuidebookLike.objects.all().values('guidebook').annotate()
                guidebook_ary = []
                if guidebook_likes.count() > 0:
                    for guidebook_like in guidebook_likes:
                        guidebook_ary.append(guidebook_like['guidebook'])
                if like == 'true':
                    guidebooks = guidebooks.filter(pk__in=guidebook_ary)
                elif like == 'false':
                    guidebooks = guidebooks.exclude(pk__in=guidebook_ary)
            if image_key is not None and image_key != '':
                scenes = Scene.objects.filter(image_key__icontains=image_key)
                guidebook_id_ary = []
                if scenes.count() > 0:
                    for s in scenes:
                        guidebook_id_ary.append(s.guidebook_id)
                guidebooks = guidebooks.filter(pk__in=guidebook_id_ary)

    if guidebooks is None:
        guidebooks = Guidebook.objects.all().filter(is_published=True, is_approved=True)
        form = GuidebookSearchForm()

    request.session['guidebooks_query'] = get_correct_sql(guidebooks)

    if order_type == 'most_likes':
        paginator = Paginator(guidebooks.order_by('-like_count', '-created_at'), 10)
    else:
        paginator = Paginator(guidebooks.order_by('-created_at'), 10)

    try:
        p_guidebooks = paginator.page(page)
    except PageNotAnInteger:
        p_guidebooks = paginator.page(1)
    except EmptyPage:
        p_guidebooks = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if p_guidebooks.number < 4:
            first_num = 1
            last_num = 7
        elif p_guidebooks.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = p_guidebooks.number - 3
            last_num = p_guidebooks.number + 3
    p_guidebooks.paginator.pages = range(first_num, last_num + 1)
    p_guidebooks.count = len(p_guidebooks)
    content = {
        'guidebooks': p_guidebooks,
        'form': form,
        'pageName': 'Guidebooks',
        'pageTitle': 'Guidebooks',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page,
        'order_type': order_type
    }
    return render(request, 'guidebook/guidebook_list.html', content)


# noinspection DuplicatedCode,PyProtectedMember
@my_login_required
def my_guidebook_list(request):
    global form
    guidebooks = None
    page = 1
    order_type = 'latest_at'
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        order_type = request.GET.get('order_type')
        form = GuidebookSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            category = form.cleaned_data['category']
            tags = form.cleaned_data['tag']
            image_key = form.cleaned_data['image_key']
            like = form.cleaned_data['like']

            guidebooks = Guidebook.objects.all().filter(
                user=request.user
            )
            if name is not None and name != '':
                guidebooks = guidebooks.filter(name__icontains=name)
            if category is not None and category != '':
                guidebooks = guidebooks.filter(category__name=category)

            if len(tags) > 0:
                for tag in tags:
                    guidebooks = guidebooks.filter(tag=tag)

            if like and like != 'all':
                guidebook_likes = GuidebookLike.objects.all().values('guidebook').annotate()
                print(guidebook_likes)
                guidebook_ary = []
                if guidebook_likes.count() > 0:
                    for guidebook_like in guidebook_likes:
                        guidebook_ary.append(guidebook_like['guidebook'])
                if like == 'true':
                    guidebooks = guidebooks.filter(pk__in=guidebook_ary)
                elif like == 'false':
                    guidebooks = guidebooks.exclude(pk__in=guidebook_ary)

            if image_key is not None and image_key != '':
                scenes = Scene.objects.filter(image_key__icontains=image_key)
                guidebook_id_ary = []
                if scenes.count() > 0:
                    for s in scenes:
                        guidebook_id_ary.append(s.guidebook_id)
                guidebooks = guidebooks.filter(pk__in=guidebook_id_ary)

    if guidebooks is None:
        guidebooks = Guidebook.objects.all().filter(
            user=request.user
        )
        form = GuidebookSearchForm()

    request.session['guidebooks_query'] = get_correct_sql(guidebooks)

    if order_type == 'most_likes':
        paginator = Paginator(guidebooks.order_by('-like_count', '-created_at'), 10)
    else:
        paginator = Paginator(guidebooks.order_by('-created_at'), 10)

    try:
        p_guidebooks = paginator.page(page)
    except PageNotAnInteger:
        p_guidebooks = paginator.page(1)
    except EmptyPage:
        p_guidebooks = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if p_guidebooks.number < 4:
            first_num = 1
            last_num = 7
        elif p_guidebooks.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = p_guidebooks.number - 3
            last_num = p_guidebooks.number + 3
    p_guidebooks.paginator.pages = range(first_num, last_num + 1)
    p_guidebooks.count = len(p_guidebooks)
    form._my(request.user.username)
    content = {
        'guidebooks': p_guidebooks,
        'form': form,
        'pageName': 'My Guidebooks',
        'pageTitle': 'My Guidebooks',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page,
        'order_type': order_type
    }
    return render(request, 'guidebook/guidebook_list.html', content)


def guidebook_detail(request, unique_id):
    guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
    if not guidebook.is_published and request.user != guidebook.user:
        messages.error(request, 'The guidebook is not published.')
        return redirect('guidebook.guidebook_list')
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
    firstImageKey = guidebook.getFirstScene()
    if not firstImageKey is None and firstImageKey != '':
        firstImageKey = firstImageKey.image_key
    content = {
        'guidebook': guidebook,
        'is_liked': is_liked,
        'form': form,
        'poi_form': poi_form,
        'pageTitle': guidebook.name + ' - ' + 'Guidebook',
        'pageDescription': guidebook.description,
        'pageName': 'Guidebook Detail',
        'firstImageKey': firstImageKey
    }
    return render(request, 'guidebook/guidebook_detail.html', content)


@my_login_required
def guidebook_create(request, unique_id=None):
    image_key = ''
    if request.method == "POST":
        form = GuidebookForm(request.POST, request.FILES)

        if form.is_valid():
            if unique_id is None:
                guidebook = form.save(commit=False)
                guidebook.user = request.user
                guidebook.save()
                if form.cleaned_data['tag'].count() > 0:
                    for tag in form.cleaned_data['tag']:
                        guidebook.tag.add(tag)
                    for tag in guidebook.tag.all():
                        if tag not in form.cleaned_data['tag']:
                            guidebook.tag.remove(tag)
            else:
                guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
                guidebook.name = form.cleaned_data['name']
                guidebook.description = form.cleaned_data['description']
                guidebook.cover_image = form.cleaned_data['cover_image']
                guidebook.category = form.cleaned_data['category']

                if form.cleaned_data['tag'].count() > 0:
                    for tag in form.cleaned_data['tag']:
                        guidebook.tag.add(tag)
                    for tag in guidebook.tag.all():
                        if tag not in form.cleaned_data['tag']:
                            guidebook.tag.remove(tag)
                guidebook.save()

            image_key = request.POST.get('image_key', '')
            messages.success(request, 'A guidebook was created successfully.')
            if image_key == '':
                return redirect('guidebook.add_scene', unique_id=guidebook.unique_id)
            else:
                return redirect(reverse('guidebook.add_scene', kwargs={'unique_id': guidebook.unique_id}) + '?image_key=' + image_key)
        else:
            errors = []
            for field in form:
                for error in field.errors:
                    errors.append(field.name + ': ' + error)
            return JsonResponse({
                'status': 'failed',
                'message': '<br>'.join(errors)
            })

    else:
        if unique_id:
            guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
            form = GuidebookForm(instance=guidebook)
        else:
            form = GuidebookForm()
        image_key = request.GET.get('image_key', '')
    content = {
        'form': form,
        'image_key': image_key,
        'pageName': 'Create Guidebook',
        'pageTitle': 'Create Guidebook',
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }
    return render(request, 'guidebook/create_main.html', content)


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
            if form.cleaned_data['tag'].count() > 0:
                for tag in form.cleaned_data['tag']:
                    guidebook.tag.add(tag)
                for tag in guidebook.tag.all():
                    if tag not in form.cleaned_data['tag']:
                        guidebook.tag.remove(tag)
            guidebook.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Guidebook was uploaded successfully.',
                'guidebook': {
                    'title': guidebook.name,
                    'description': guidebook.description,
                    'category': guidebook.category.name,
                    'tag': guidebook.get_tags()
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
    content = {
        'guidebook': guidebook,
        'g_form': g_form,
        'form': form,
        'poi_form': poi_form,
        'pageName': 'Edit Guidebook',
        'pageTitle': 'Edit Guidebook',
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }
    return render(request, 'guidebook/add_scene.html', content)


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
        'message': 'The Guidebook does not exist or has no access.'
    })


@my_login_required
def ajax_upload_scene_image(request, unique_id, scene_id):
    guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
    if guidebook.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't access."
        })

    if request.method == "POST":
        scene = Scene.objects.filter(guidebook=guidebook, pk=scene_id).first()
        if scene is None:
            return JsonResponse({
                'status': 'failed',
                'message': "Scene doesn't exist."
            })

        form = SceneImageForm(request.POST, request.FILES)
        if form.is_valid():
            form_data = form.save(commit=False)
            scene.image = form_data.image
            scene.video_url = ''
            scene.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Picture is uploaded successfully.',
                'poi_image': '',
                'poi_video': '',
                'scene_image': scene.image.url,
                'scene_video': ''
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
        'message': "You can't access."
    })


@my_login_required
def ajax_upload_scene_video(request, unique_id, scene_id):
    guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
    if guidebook.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't access."
        })

    if request.method == "POST":
        scene = Scene.objects.filter(guidebook=guidebook, pk=scene_id).first()
        if scene is None:
            return JsonResponse({
                'status': 'failed',
                'message': "Scene doesn't exist."
            })

        form = SceneVideoForm(request.POST)
        if form.is_valid():
            video_url = form.cleaned_data['video_url']
            scene.video_url = get_youtube_embed_url(video_url)
            scene.image = None
            scene.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Video URL is saved successfully.',
                'poi_image': '',
                'poi_video': '',
                'scene_image': '',
                'scene_video': scene.video_url
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
        'message': "You can't access."
    })


@my_login_required
def ajax_scene_media_delete(request, unique_id, scene_id):
    guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
    if guidebook.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't access."
        })

    if request.method == "POST":
        scene = Scene.objects.filter(guidebook=guidebook, pk=scene_id).first()
        if scene is None:
            return JsonResponse({
                'status': 'failed',
                'message': "Scene doesn't exist."
            })

        scene.video_url = ''
        if bool(scene.image):
            scene.image.delete(save=True)
        scene.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Media is deleted successfully.',
        })

    return JsonResponse({
        'status': 'failed',
        'message': "You can't access."
    })


@my_login_required
def ajax_upload_poi_image(request, unique_id, scene_id, poi_id):
    guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
    if guidebook.user != request.user:
        messages.error(request, "You can't access the page.")
        return redirect('/')

    if request.method == "POST":
        scene = Scene.objects.filter(guidebook=guidebook, pk=scene_id).first()
        if scene is None:
            return JsonResponse({
                'status': 'failed',
                'message': "Scene doesn't exist."
            })

        poi = PointOfInterest.objects.filter(scene=scene, pk=poi_id).first()
        if poi is None:
            return JsonResponse({
                'status': 'failed',
                'message': "Poi doesn't exist."
            })


        form = PoiImageForm(request.POST, request.FILES)
        if form.is_valid():
            form_data = form.save(commit=False)
            poi.image = form_data.image
            poi.video_url = ''
            poi.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Picture is uploaded successfully.',
                'poi_image': poi.image.url,
                'poi_video': '',
                'scene_image': '',
                'scene_video': ''
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
        'message': "You can't access."
    })


@my_login_required
def ajax_upload_poi_video(request, unique_id, scene_id, poi_id):
    guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
    if guidebook.user != request.user:
        messages.error(request, "You can't access the page.")
        return redirect('/')

    if request.method == "POST":
        scene = Scene.objects.filter(guidebook=guidebook, pk=scene_id).first()
        if scene is None:
            return JsonResponse({
                'status': 'failed',
                'message': "Scene doesn't exist."
            })
        poi = PointOfInterest.objects.filter(scene=scene, pk=poi_id).first()
        if poi is None:
            return JsonResponse({
                'status': 'failed',
                'message': "Poi doesn't exist."
            })

        form = PoiVideoForm(request.POST)
        if form.is_valid():
            video_url = form.cleaned_data['video_url']
            poi.video_url = get_youtube_embed_url(video_url)
            poi.image = None
            poi.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Video URL is saved successfully.',
                'poi_image': '',
                'poi_video': poi.video_url,
                'scene_image': '',
                'scene_video': ''
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
        'message': "You can't access."
    })


@my_login_required
def ajax_poi_media_delete(request, unique_id, scene_id, poi_id):
    guidebook = get_object_or_404(Guidebook, unique_id=unique_id)
    if guidebook.user != request.user:
        messages.error(request, "You can't access the page.")
        return redirect('/')

    if request.method == "POST":
        scene = Scene.objects.filter(guidebook=guidebook, pk=scene_id).first()
        if scene is None:
            return JsonResponse({
                'status': 'failed',
                'message': "Scene doesn't exist."
            })
        poi = PointOfInterest.objects.filter(scene=scene, pk=poi_id).first()
        if poi is None:
            return JsonResponse({
                'status': 'failed',
                'message': "Poi doesn't exist."
            })

        poi.video_url = ''
        poi.image = None
        poi.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Media is deleted successfully.',
        })

    return JsonResponse({
        'status': 'failed',
        'message': "You can't access."
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
            username = form.cleaned_data['username']

            if scene:
                old_scene = scene[0]
                old_scene.title = title
                old_scene.description = description
                old_scene.lat = lat
                old_scene.lng = lng
                old_scene.point = Point(lat, lng)
                old_scene.username = username
                old_scene.save()

                scene_external_html = render_to_string(
                    'guidebook/scene_external_edit_box.html',
                    {'scene': old_scene},
                    request
                )

                scene_json = serializers.serialize('json', [old_scene, ])
                json_scene = json.loads(scene_json)


                return JsonResponse({
                    'type': 'update',
                    'scene_id': old_scene.pk,
                    'title': old_scene.title,
                    'description': old_scene.description,
                    'scene': json_scene,
                    'scene_external_html': scene_external_html,
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
                new_scene.point = Point(lat, lng)
                new_scene.username = username
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
                    if scene_count == 1:
                        guidebook.is_published = True
                        guidebook.save()
                else:
                    scene_count = 0

                scene_external_html = render_to_string(
                    'guidebook/scene_external_edit_box.html',
                    {'scene': new_scene},
                    request
                )

                scene_json = serializers.serialize('json', [new_scene, ])
                json_scene = json.loads(scene_json)

                return JsonResponse({
                    'type': 'new',
                    'scene_id': new_scene.pk,
                    'scene_box_html': scene_box_html,
                    'scene_count': scene_count,
                    'scene': json_scene,
                    'scene_external_html': scene_external_html,
                    'status': 'success',
                    'message': 'A new Scene is added successfully.'
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
            poi.title = ''
            poi.description = ''
            categories = POICategory.objects.all()
            poi.category_id = categories[0].pk
            poi.position_x = request.POST.get('position_x')
            poi.position_y = request.POST.get('position_y')
            poi.scene = scene
            poi.image = None
            poi.video_url = ''
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
            'poi_count': scene.get_poi_count(),
            'message': message
        })

    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to save Point of Interest!'
    })


@my_login_required
def ajax_add_scene_external_url(request, unique_id, pk):
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
        external_url = request.POST.get('external_url')
        if external_url is None or external_url == '':
            return JsonResponse({
                'status': 'failed',
                'message': 'External URL is required.'
            })

        external_url_obj = SceneExternalURL()
        external_url_obj.external_url = external_url
        external_url_obj.save()
        scene.external_url.add(external_url_obj)
        scene.save()

        message = 'External URL is successfully added.'

        return JsonResponse({
            'status': 'success',
            'message': message,
            'external_url_id': external_url_obj.pk,
            'short_external_url': external_url_obj.short_external_url()
        })

    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to add External URL!'
    })


@my_login_required
def ajax_delete_scene_external_url(request, unique_id, pk):
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

        external_url_id = request.POST.get('external_url_id')
        if external_url_id is None or external_url_id == '':
            return JsonResponse({
                'status': 'failed',
                'message': 'External URL is required.'
            })

        external_url = scene.external_url.filter(pk=external_url_id).first()
        if external_url is not None:
            external_url.delete()

            message = 'External URL is successfully deleted.'

            return JsonResponse({
                'status': 'success',
                'message': message,
            })

    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to delete External URL!'
    })


@my_login_required
def ajax_add_external_url(request, unique_id, pk):
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
        external_url = request.POST.get('external_url')
        if external_url is None or external_url == '':
            return JsonResponse({
                'status': 'failed',
                'message': 'External URL is required.'
            })

        external_url_obj = POIExternalURL()
        external_url_obj.external_url = external_url
        external_url_obj.save()
        poi.external_url.add(external_url_obj)
        poi.save()

        message = 'External URL is successfully added.'

        return JsonResponse({
            'status': 'success',
            'message': message,
            'poi_count': scene.get_poi_count(),
            'external_url_id': external_url_obj.pk,
            'short_external_url': external_url_obj.short_external_url()
        })

    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to delete Point of Interest!'
    })


@my_login_required
def ajax_delete_external_url(request, unique_id, pk):
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
        external_url_id = request.POST.get('external_url_id')
        if external_url_id is None or external_url_id == '':
            return JsonResponse({
                'status': 'failed',
                'message': 'External URL is required.'
            })

        external_url = poi.external_url.filter(pk=external_url_id).first()
        if external_url is not None:
            external_url.delete()

        message = 'External URL is successfully deleted.'

        return JsonResponse({
            'status': 'success',
            'message': message,
        })

    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to delete External URL of Interest!'
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
            'message': message,
            'poi_count': scene.get_poi_count()
        })

    return JsonResponse({
        'status': 'failed',
        'message': 'It failed to delete Point of Interest!'
    })


def ajax_get_scene(request, unique_id):
    image_key = request.GET.get('image_key', None)
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist or has no access.'
        })

    scene = Scene.objects.filter(guidebook=guidebook, image_key=image_key)
    if not scene or scene.count() == 0 or image_key is None:
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

        scene_external_html = render_to_string(
            'guidebook/scene_external_box.html',
            {'scene': scene_first},
            request
        )

        scene_json = serializers.serialize('json', [scene_first, ])
        json_scene = json.loads(scene_json)

        return JsonResponse({
            'status': 'success',
            'scene': json_scene,
            'poi_list': poi_list,
            'scene_external_html': scene_external_html
        })


@my_login_required
def ajax_get_edit_scene(request, unique_id):
    image_key = request.GET['image_key']
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook and guidebook.user != request.user:
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
            for sss in poi.external_url.all():
                print(sss.external_url)
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

        scene_external_html = render_to_string(
            'guidebook/scene_external_edit_box.html',
            {'scene': scene_first},
            request
        )

        scene_json = serializers.serialize('json', [scene_first, ])
        json_scene = json.loads(scene_json)

        return JsonResponse({
            'status': 'success',
            'scene': json_scene,
            'poi_list': poi_list,
            'scene_external_html': scene_external_html
        })


@my_login_required
def ajax_set_start_view(request, unique_id):
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if not guidebook and guidebook.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Guidebook does not exist or has no access.'
        })

    if request.method == 'POST':
        image_key = request.POST['image_key']
        scenes = Scene.objects.filter(guidebook=guidebook, image_key=image_key)
        if not scenes or scenes.count() == 0:
            return JsonResponse({
                'status': 'failed',
                'message': 'The scene does not exist or has no access.'
            })
        else:
            scene = scenes[0]
            start_x = request.POST['start_x']
            if start_x is None:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The derection information is empty.'
                })
            else:
                scene.start_x = start_x

            start_y = request.POST['start_y']
            if start_y is None:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The derection information is empty.'
                })
            else:
                scene.start_y = start_y

            scene.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Starting view is successfully set.'
            })
    return JsonResponse({
        'status': 'failed',
        'message': 'Bad request'
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
        points_of_interest = PointOfInterest.objects.filter(scene=scene)
        if points_of_interest and points_of_interest.count() > 0:
            for p in points_of_interest:
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

    if not guidebook.is_published:
        return JsonResponse({
            'status': 'failed',
            'message': "This guidebook is not published."
        })

    guidebook_like = GuidebookLike.objects.filter(guidebook=guidebook, user=request.user)
    if guidebook_like:
        if guidebook.user.is_liked_email:
            # confirm email
            try:
                # send email to creator
                subject = 'Your Map the Paths Guidebook Was Liked'
                html_message = render_to_string(
                    'emails/guidebook/like.html',
                    {'subject': subject, 'like': 'unliked', 'guidebook': guidebook, 'sender': request.user},
                    request
                )
                send_mail_with_html(subject, html_message, guidebook.user.email, settings.SMTP_REPLY_TO)
            except:
                print('email sending error!')
        for g in guidebook_like:
            g.delete()
        liked_guidebook = GuidebookLike.objects.filter(guidebook=guidebook)
        if not liked_guidebook:
            liked_count = 0
        else:
            liked_count = liked_guidebook.count()
        guidebook.like_count = liked_count
        guidebook.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Unliked',
            'is_checked': False,
            'liked_count': liked_count
        })
    else:
        if guidebook.user.is_liked_email:
            try:
                # send email to creator
                subject = 'Your Map the Paths Guidebook Was Liked'
                html_message = render_to_string(
                    'emails/guidebook/like.html',
                    {'subject': subject, 'like': 'liked', 'guidebook': guidebook, 'sender': request.user},
                    request
                )
                send_mail_with_html(subject, html_message, guidebook.user.email, settings.SMTP_REPLY_TO)
            except:
                print('email sending error!')
        guidebook_like = GuidebookLike()
        guidebook_like.guidebook = guidebook
        guidebook_like.user = request.user
        guidebook_like.save()
        liked_guidebook = GuidebookLike.objects.filter(guidebook=guidebook)
        if not liked_guidebook:
            liked_count = 0
        else:
            liked_count = liked_guidebook.count()
        guidebook.like_count = liked_count
        guidebook.save()
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
    return redirect('guidebook.guidebook_list')


def ajax_get_detail(request, unique_id):
    guidebook = Guidebook.objects.get(unique_id=unique_id)
    if guidebook.user == request.user:
        is_mine = True
    else:
        is_mine = False
    serialized_obj = serializers.serialize('json', [guidebook, ])
    data = {
        'guidebook': json.loads(serialized_obj)
    }

    if not data['guidebook']:
        data['message'] = "The guidebook id doesn't exist."
    else:
        data['guidebook_html_detail'] = render_to_string('guidebook/modal_detail.html', {'guidebook': guidebook, 'is_mine': is_mine})

    return JsonResponse(data)


def ajax_get_detail_by_image_key(request, image_key):
    print(image_key)
    scenes = Scene.objects.filter(image_key=image_key)
    print(scenes.count())
    if scenes.count() == 0:
        return JsonResponse({
            'status': 'failed',
            'message': "Image key error."
        })

    guidebooks = []
    data = {}
    for scene in scenes:
        guidebook = scene.guidebook
        guidebooks.append(guidebook)

    data['guidebook_html_detail'] = render_to_string('guidebook/modal_detail.html', {'guidebooks': guidebooks})

    return JsonResponse(data)
