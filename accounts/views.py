
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Min, Sum
from django.db.models.expressions import F, Window
from django.db.models.functions.window import RowNumber

from datetime import datetime
from mailerlite import MailerLiteApi
import secrets
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)
from lib.functions import *
from lib.badge import get_finder_label, get_guidebook_label, get_mapper_label, get_spotter_label

from .models import CustomUser, MapillaryUser
from .forms import UserSignUpForm, UserProfileForm, UserAvatarForm, UserUpdateForm
from sequence.models import Sequence, ImageViewPoint, SequenceLike
from tour.models import Tour, TourLike
from guidebook.models import Guidebook, GuidebookLike
UserModel = get_user_model()
import requests

def signup(request):
    if request.method == "POST":
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            authenticate(email=email, password=password)
            if user != None:
                user.verify_email_key = secrets.token_urlsafe(50)
                user.save()

                # confirm email 
                try:
                    # send email to creator
                    subject = 'Please confirm your email'
                    html_message = render_to_string(
                        'emails/account/signup_email_confirm.html', 
                        { 'subject': subject, 'url': '/accounts/email-verify/' + user.verify_email_key}, 
                        request
                    )
                    send_mail_with_html(subject, html_message, email)
                except:
                    print('email sending error!')


                # add maillist
                if user.is_maillist:
                    mailerAPI = MailerLiteApi(settings.MAILERLIST_API_KEY)
                    data = [{
                        'email': user.email,
                        'name': user.username
                    }]
                    try:
                        print(mailerAPI.groups.add_subscribers(group_id=settings.MAILERLIST_GROUP_ID, subscribers_data=data))
                    except:
                        pass
                messages.success(request, 'Please check inbox to confirm your email address.')
                return redirect('login')
    else:
        form = UserSignUpForm()
    return render(request, 'signup.html', {'form': form})

def email_verify(request, key):
    user = CustomUser.objects.get(verify_email_key=key)
    if user:
        user.is_active = True
        user.save()

        # confirm email successfully
        try:
            # send email to creator
            subject = 'Your account is confirmed successfully'
            html_message = render_to_string(
                'emails/account/signup_email_confirmed.html', 
                { 'subject': subject}, 
                request
            )
            send_mail_with_html(subject, html_message, user.email)
        except:
            print('email sending error!')
        messages.success(request, 'Your account is confirmed. You can now login.')
    else:
        messages.error(request, 'Error, invalid token!')
    return redirect('login')
    # return render(request, 'registration/confirm_template.html', {'success': False})

@my_login_required
def profile_edit(request):
    user = request.user
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.updated_at = datetime.now()
            user.save()
            messages.success(request, 'Your email is updated successfully.')
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'account/index.html', {'form': form, 'pageName': 'Profile'})

def change_password_success(request):
    messages.success(request, 'Your password is updated successfully.')
    return redirect('change_password')

@my_login_required
def check_mapillary_oauth(request):
    if request.method == 'GET':
        mapillary_access_token = request.GET.get('access_token')
        if mapillary_access_token is None or mapillary_access_token == '':
            return redirect('sequence.index')
        user = request.user
        user.mapillary_access_token = mapillary_access_token
        user.save()

        map_user_data = check_mapillary_token(request.user)

        if not map_user_data:
            messages.error(request, "Unauthorized for Mapillary")
            return redirect('home')

        data = MapillaryUser.objects.filter(key=map_user_data['key'], user=request.user)
        if data.count() == 0:
            map_user = MapillaryUser()
        else:
            map_user = data[0]

        if 'about' in map_user_data:
            map_user.about = map_user_data['about']
        if 'avatar' in map_user_data:
            map_user.avatar = map_user_data['avatar']
        if 'created_at' in map_user_data:
            map_user.created_at = map_user_data['created_at']
        if 'email' in map_user_data:
            map_user.email = map_user_data['email']
        if 'key' in map_user_data:
            map_user.key = map_user_data['key']
        if 'username' in map_user_data:
            map_user.username = map_user_data['username']

        map_user.user = request.user
        map_user.save()
        return redirect('sequence.import_sequence_list')
    else:
        messages.error(request, 'Error, mapillary invalid token!')
        return redirect('home')

def profile(request, username):
    user = get_object_or_404(CustomUser, username=username)
    form = UserUpdateForm(instance=user)

    sequences = Sequence.objects.filter(user=user, is_published=True).exclude(image_count=0)
    imageCount = 0
    imageViewPointCount = 0
    sequenceLikeCount = 0
    sequenceCount = sequences.count()
    if sequenceCount > 0:

        image_key_ary = []
        for sequence in sequences:
            sequenceLikes = SequenceLike.objects.filter(sequence=sequence)
            sequenceLikeCount += sequenceLikes.count()

            imageCount += sequence.image_count
            image_key_ary += sequence.coordinates_image

        imageViewPoints = ImageViewPoint.objects.filter(image__image_key__in=image_key_ary)
        imageViewPointCount = imageViewPoints.count()

    markedImageViewPoints = ImageViewPoint.objects.filter(user=user)
    markedImageViewPointCount = markedImageViewPoints.count()

    guidebooks = Guidebook.objects.filter(user=user, is_published=True)
    guidebookCount = guidebooks.count()
    guidebookLikeCount = 0
    if guidebookCount > 0:
        for guidebook in guidebooks:
            guidebookLikes = GuidebookLike.objects.filter(guidebook=guidebook)
            guidebookLikeCount += guidebookLikes.count()

    tours = Tour.objects.filter(user=user, is_published=True)
    tourCount = tours.count()
    tourLikeCount = 0
    if tourCount > 0:
        for tour in tours:
            tourLikes = TourLike.objects.filter(tour=tour)
            tourLikeCount += tourLikes.count()

    mapper_label = get_mapper_label(imageCount)
    guidebook_label = get_guidebook_label(guidebookCount)
    finder_label = get_finder_label(imageViewPointCount)
    spotter_label = get_spotter_label()



    content = {
        'current_user': user,
        'username': username,
        'form': form,
        'mapper_label': mapper_label,
        'guidebook_label': guidebook_label,
        'finder_label': finder_label,
        'spotter_label': spotter_label,
        'sequences_count': sequenceCount,
        'seq_like_count': sequenceLikeCount,
        'tours_count': tourCount,
        'tour_like_count': tourLikeCount,
        'guidebooks_count': guidebookCount,
        'guide_like_count': guidebookLikeCount,
        'view_point_count': imageViewPointCount,
        'marked_point_count': markedImageViewPointCount,
        'pageName': 'Profile',
        'pageTitle': 'Profile'
    }

    return render(request, 'account/profile.html', content)

@my_login_required
def ajax_upload_file(request):
    user = request.user

    if request.method == "POST":
        form = UserAvatarForm(request.POST, request.FILES)
        if form.is_valid():
            form_data = form.save(commit=False)
            user.avatar = form_data.avatar
            user.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Picture is uploaded successfully.'
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
def ajax_user_update(request):
    user = request.user

    if request.method == "POST":

        email = request.POST.get('email')
        if email is None:
            return JsonResponse({
                'status': 'failed',
                'message': "Email is missing."
            })
        users = CustomUser.objects.filter(email=email).exclude(username=user.username)
        if users.count() > 0:
            return JsonResponse({
                'status': 'failed',
                'message': "The email is already exist."
            })
        else:
            user.email = email

        first_name = request.POST.get('first_name')
        print('first_name', first_name)
        if first_name is None:
            return JsonResponse({
                'status': 'failed',
                'message': "First Name is required."
            })
        else:
            user.first_name = first_name
            last_name = request.POST.get('last_name')
            if last_name is None:
                return JsonResponse({
                    'status': 'failed',
                    'message': "Last Name is required."
                })
            else:
                user.last_name = last_name
        if not request.POST.get('description') is None:
            user.description = request.POST.get('description')

        if not request.POST.get('website_url') is None:
            user.website_url = request.POST.get('website_url')
        user.save()

        return JsonResponse({
            'status': 'success',
            'message': 'User detail data was uploaded successfully.',
            'user': {
                'email': user.email,
                'description': user.description,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'website_url': user.website_url
            }
        })


    return JsonResponse({
        'status': 'failed',
        'message': "You can't access."
    })
