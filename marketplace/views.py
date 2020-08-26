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

def home(request):
    return redirect('marketplace.job_list', page=1)

@my_login_required
def job_create(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            job.save()
            geometry = json.loads(job.geometry)
            for geo in geometry:
                geo['properties']['job_id'] = str(job.unique_id)
            job.geometry = json.dumps(geometry)
            job.save()

            try:
                # send email to creator
                subject = 'Your job post is under review'
                html_message = render_to_string(
                    'emails/marketplace/job/create.html', 
                    { 'subject': subject, 'job': job}, 
                    request
                )
                send_mail_with_html(subject, html_message, request.user.email)
                # send email to admin
                staffs = CustomUser.objects.filter(is_staff=True, is_active=True)
                staff_emails = []
                for staff in staffs:
                    staff_emails.append(staff.email)
                if len(staff_emails) > 0:
                    subject = 'Job post needs to be approved'
                    html_message = render_to_string(
                        'emails/marketplace/job/create_admin.html', 
                        { 'subject': subject, 'job': job}, 
                        request
                    )
                    send_mail_with_html(subject, html_message, staff_emails)
            except:
                print('email sending error!')
            
            messages.success(request, 'A job was created successfully.')
            return redirect('marketplace.my_job_list')
    else:
        form = JobForm()
    content = {
        'form': form,
        'pageName': 'Create Job',
        'pageTitle': 'Marketplace',
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }
    return render(request, 'marketplace/job/create.html', content)

@my_login_required
def job_apply(request, unique_id):
    job = get_object_or_404(Job, unique_id=unique_id)
    if request.method == "POST":
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            jobApply = form.save(commit=False)
            jobApply.job = job
            jobApply.user = request.user
            jobApply.email = request.user.email
            jobApply.save()

            try:
                # send email to applicant
                subject = jobApply.subject + ' has been sent'
                html_message = render_to_string(
                    'emails/marketplace/job/apply_applicant.html', 
                    { 'subject': subject, 'job': job, 'job_apply': jobApply}, 
                    request
                )
                send_mail_with_html(subject, html_message, request.user.email)
                
                # send email to job creator
                subject = request.user.username + ' applied for "' + job.name + '"'
                html_message = render_to_string(
                    'emails/marketplace/job/apply_creator.html', 
                    { 'subject': subject, 'job': job, 'job_apply': jobApply}, 
                    request
                )
                send_mail_with_html(subject, html_message, job.user.email)
            except:
                print('email sending error!')


            messages.success(request, 'You have successfully applied for a job.')
            return redirect('marketplace.job_list')
    else:
        form = JobApplicationForm()
    content = {
        'form': form,
        'job': job,
        'pageName': 'Apply Job',
        'pageTitle': 'Job'
    }
    return render(request, 'marketplace/job/apply.html', content)

@my_login_required
def job_edit(request, unique_id):
    job = get_object_or_404(Job, unique_id=unique_id)
    if job.is_approved:
        is_approved = 'approved'
    else:
        is_approved = 'unapproved'
    if request.method == "POST":

        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            job.updated_at = datetime.now()
            job.save()
            geometry = json.loads(job.geometry)
            for geo in geometry:
                geo['properties']['job_id'] = str(job.unique_id)
            job.geometry = json.dumps(geometry)
            job.save()
            messages.success(request, 'Job "%s" is updated successfully.' % job.name)
            form.set_is_approved(is_approved=is_approved)
            return redirect('marketplace.home')
    else:
        form = JobForm(instance=job)
        form.set_is_approved(is_approved=is_approved)
    content = {
        'form': form,
        'pageName': 'Edit Job',
        'pageTitle': 'Job'
    }
    return render(request, 'marketplace/job/edit.html', content)

@my_login_required
def my_job_delete(request, unique_id):
    job = get_object_or_404(Job, unique_id=unique_id)
    if job.user == request.user:
        job.delete()
        messages.success(request, 'Job "%s" is deleted successfully.' % job.name)
    else:
        messages.error(request, "This user hasn't permission")
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def job_list(request, page):
    jobs = None
    if request.method == "GET":
        form = JobSearchForm(request.GET)

        if form.is_valid():
            type = form.cleaned_data['type']
            captureMethod = form.cleaned_data['capture_method']
            jobs = Job.objects.all().filter(is_published=True, is_approved=True)
            if len(type) > 0:
                jobs = jobs.filter(type__overlap=type)
            if len(captureMethod) > 0:
                jobs = jobs.filter(capture_method__overlap=captureMethod)

            
    if jobs == None:
        jobs = Job.objects.all().filter(is_published=True, is_approved=True)
        form = JobSearchForm()

    paginator = Paginator(jobs.order_by('-created_at'), 10)

    try:
        pJobs = paginator.page(page)
    except PageNotAnInteger:
        pJobs = paginator.page(1)
    except EmptyPage:
        pJobs = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pJobs.number < 4:
            first_num = 1
            last_num = 7
        elif pJobs.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pJobs.number - 3
            last_num = pJobs.number + 3
    pJobs.paginator.pages = range(first_num, last_num + 1)
    pJobs.count = len(pJobs)
    content = {
        'jobs': jobs,
        'form': form,
        'pageName': 'Jobs',
        'pageTitle': 'Marketplace',
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }
    return render(request, 'marketplace/job/list.html', content)

def job_detail(request, unique_id):
    job = get_object_or_404(Job, unique_id=unique_id)
    if not job.is_approved and job.user != request.user:
        messages.success(request, "Job \"%s\" isn't approved." % job.name)
        return redirect('marketplace.job_list')

    if (not request.user.is_authenticated or request.user != job.user) and not job.is_published:
        messages.success(request, "You can't access this job.")
        return redirect('marketplace.job_list')

    form = JobSearchForm()

    geometry = json.dumps(job.geometry)

    if job.user == request.user:
        is_mine = True

    else:
        is_mine = False

    job.options = job.getOrganisationCategory() + ', ' + job.getCaptureType() + ', ' + job.getCaptureMethod()
    apply_url = reverse('marketplace.job_apply', kwargs={'unique_id': str(job.unique_id)})
    job_html_detail = render_to_string('marketplace/job/modal_detail.html', {'job': job, 'apply_url': apply_url, 'is_mine': is_mine})
    content = {
        'job': job,
        'form': form,
        'geometry': geometry,
        'job_html_detail': job_html_detail,
        'pageName': 'Job Detail',
        'pageTitle': 'Job'
    }
    return render(request, 'marketplace/job/job_detail.html', content)

@my_login_required
def my_job_list(request, page):
    jobs = None
    if request.method == "GET":
        form = JobSearchForm(request.GET)

        if form.is_valid():

            type = form.cleaned_data['type']
            captureMethod = form.cleaned_data['capture_method']
            image_quality = form.cleaned_data['image_quality']

            jobs = Job.objects.all().filter(user=request.user)
            if len(type) > 0:
                jobs = jobs.filter(type__overlap=type)
            if len(captureMethod) > 0:
                jobs = jobs.filter(capture_method__overlap=captureMethod)

            if (image_quality != ''):
                jobs = jobs.filter(image_quality=image_quality)
            
    if jobs == None:
        jobs = Job.objects.all().filter(user=request.user)
        form = JobSearchForm()

    paginator = Paginator(jobs.order_by('-created_at'), 10)

    try:
        pJobs = paginator.page(page)
    except PageNotAnInteger:
        pJobs = paginator.page(1)
    except EmptyPage:
        pJobs = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pJobs.number < 4:
            first_num = 1
            last_num = 7
        elif pJobs.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pJobs.number - 3
            last_num = pJobs.number + 3
    pJobs.paginator.pages = range(first_num, last_num + 1)
    pJobs.count = len(pJobs)

    content = {
        'jobs': pJobs,
        'form': form,
        'pageName': 'My Jobs',
        'pageTitle': 'Marketplace',
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }
    return render(request, 'marketplace/job/list.html', content)

def ajax_job_detail(request, unique_id):
    job = Job.objects.get(unique_id=unique_id)
    if job.user == request.user:
        is_mine = True

    else:
        is_mine = False
    serialized_obj = serializers.serialize('json', [job, ])
    data = {
        'job': json.loads(serialized_obj)
    }
    
    if not data['job']:
        data['error_message'] = "The job id doesn't exist."
    else:
        job.options = job.getOrganisationCategory() + ', ' + job.getCaptureType() + ', ' + job.getCaptureMethod()
        apply_url = reverse('marketplace.job_apply', kwargs={'unique_id': str(job.unique_id)})
        data['job_html_detail'] = render_to_string('marketplace/job/modal_detail.html', {'job': job, 'apply_url': apply_url, 'is_mine': is_mine})

    return JsonResponse(data)

@my_login_required
def photographer_create(request):
    if request.method == "POST":
        form = PhotographerForm(request.POST)

        if form.is_valid():
            photographer = form.save(commit=False)
            photographer.user = request.user
            photographer.save()
            geometry = json.loads(photographer.geometry)
            for geo in geometry:
                geo['properties']['photographer_id'] = str(photographer.unique_id)
            photographer.geometry = json.dumps(geometry)
            photographer.save()
            
            try:
                # send email to creator
                subject = 'Your photographer profile is under review'
                html_message = render_to_string(
                    'emails/marketplace/photographer/create.html', 
                    { 'subject': subject, 'photographer': photographer}, 
                    request
                )
                send_mail_with_html(subject, html_message, request.user.email)

                # send email to admin
                staffs = CustomUser.objects.filter(is_staff=True, is_active=True)
                staff_emails = []
                for staff in staffs:
                    staff_emails.append(staff.email)
                if len(staff_emails) > 0:
                    subject = 'A photographer profile needs to be approved'
                    html_message = render_to_string(
                        'emails/marketplace/photographer/create_admin.html', 
                        { 'subject': subject, 'photographer': photographer}, 
                        request
                    )
                    send_mail_with_html(subject, html_message, staff_emails)
            except:
                print('email sending error!')
            
            messages.success(request, 'A photographer was created successfully.')

            return redirect('marketplace.my_photographer_list')
    else:
        form = PhotographerForm()
    content = {
        'form': form,
        'pageName': 'Create Photographer',
        'pageTitle': 'Photographer'
    }
    return render(request, 'marketplace/photographer/create.html', content)

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
                subject = photographerEnquire.subject + ' has been sent'
                html_message = render_to_string(
                    'emails/marketplace/photographer/enquire_applicant.html', 
                    { 'subject': subject, 'photographer': photographer, 'photographer_enquire': photographerEnquire}, 
                    request
                )
                send_mail_with_html(subject, html_message, request.user.email)
                
                # send email to photographer creator
                subject = request.user.username + ' hired for "' + photographer.name + '".'
                html_message = render_to_string(
                    'emails/marketplace/photographer/enquire_creator.html', 
                    { 'subject': subject, 'photographer': photographer, 'photographer_enquire': photographerEnquire}, 
                    request
                )
                send_mail_with_html(subject, html_message, photographer.user.email)
            except:
                print('email sending error!')
        
            messages.success(request, 'You have succeeded in hiring photographers.')

            return redirect('marketplace.photographer_list')
    else:
        form = PhotographerEnquireForm()
    content = {
        'form': form,
        'photographer': photographer,
        'pageName': 'Hire Photographer',
        'PageTitle': 'Photographer'
    }
    return render(request, 'marketplace/photographer/hire.html', content)

@my_login_required
def photographer_edit(request, unique_id):
    photographer = get_object_or_404(Photographer, unique_id=unique_id)
    if photographer.is_approved:
            is_approved = 'approved'
    else:
        is_approved = 'unapproved'
    if request.method == "POST":
        form = PhotographerForm(request.POST, instance=photographer)
        if form.is_valid():
            photographer = form.save(commit=False)
            photographer.user = request.user
            photographer.updated_at = datetime.now()
            photographer.save()
            geometry = json.loads(photographer.geometry)
            for geo in geometry:
                geo['properties']['photographer_id'] = str(photographer.unique_id)
            photographer.geometry = json.dumps(geometry)
            photographer.save()
            messages.success(request, 'Photographer "%s" is updated successfully.' % photographer.name)
            form.set_is_approved(is_approved=is_approved)
            return redirect('marketplace.home')
    else:
        form = PhotographerForm(instance=photographer)
        form.set_is_approved(is_approved=is_approved)
    content = {
        'form': form,
        'pageName': 'Edit Photographer',
        'pageTitle': 'Photographer'
    }
    return render(request, 'marketplace/photographer/edit.html', content)

@my_login_required
def my_photographer_delete(request, unique_id):
    photographer = get_object_or_404(Photographer, unique_id=unique_id)
    if photographer.user == request.user:
        photographer.delete()
        messages.success(request, 'Photographer "%s" is deleted successfully.' % photographer.name)
    else:
        messages.error(request, "This user hasn't permission")
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def photographer_list(request, page):
    photographers = None
    if request.method == "GET":
        form = PhotographerSearchForm(request.GET)

        if form.is_valid():

            type = form.cleaned_data['type']
            captureMethod = form.cleaned_data['capture_method']
            image_quality = form.cleaned_data['image_quality']

            photographers = Photographer.objects.all().filter(is_published=True, is_approved=True)
            if len(type) > 0:
                photographers = photographers.filter(type__overlap=type)
            if len(captureMethod) > 0:
                photographers = photographers.filter(capture_method__overlap=captureMethod)
            if (image_quality != ''):
                photographers = photographers.filter(image_quality=image_quality)
            
    if photographers == None:
        photographers = Photographer.objects.all().filter(is_published=True, is_approved=True)
        form = PhotographerSearchForm()

    paginator = Paginator(photographers.order_by('-created_at'), 10)

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
        'pageName': 'Photographers',
        'pageTitle': 'Marketplace',
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }

    return render(request, 'marketplace/photographer/list.html', content)

def photographer_detail(request, unique_id):
    photographer = get_object_or_404(Photographer, unique_id=unique_id)

    if not photographer.is_approved and request.user != photographer.user:
        messages.success(request, "Photographer \"%s\" isn't approved." % photographer.name)
        return redirect('marketplace.photographer_list')

    if (not request.user.is_authenticated or request.user != photographer.user) and not photographer.is_published:
        messages.success(request, "You can't access this photographer.")
        return redirect('marketplace.photographer_list')



    form = PhotographerSearchForm()

    geometry = json.dumps(photographer.geometry)

    if photographer.user == request.user:
        is_mine = True
    else:
        is_mine = False

    photographer.options = photographer.getCaptureType() + ', ' + photographer.getCaptureMethod()
    hire_url = reverse('marketplace.photographer_hire', kwargs={'unique_id': str(photographer.unique_id)})
    photographer_html_detail = render_to_string('marketplace/photographer/modal_detail.html', {'photographer': photographer, 'hire_url': hire_url, 'is_mine': is_mine})

    return render(request, 'marketplace/photographer/photographer_detail.html',
          {
              'photographer': photographer,
              'photographer_html_detail': photographer_html_detail,
              'form': form,
              'geometry': geometry,
              'pageName': 'Photographer Detail',
              'pageTitle': 'Photographer'
          })

@my_login_required
def my_photographer_list(request, page):
    photographers = None
    if request.method == "GET":
        form = PhotographerSearchForm(request.GET)

        if form.is_valid():
            type = form.cleaned_data['type']
            captureMethod = form.cleaned_data['capture_method']
            photographers = Photographer.objects.all().filter(user=request.user)
            if len(type) > 0:
                photographers = photographers.filter(type__overlap=type)
            if len(captureMethod) > 0:
                photographers = photographers.filter(capture_method__overlap=captureMethod)
            
    if photographers == None:
        photographers = Photographer.objects.all().filter(user=request.user)
        form = PhotographerSearchForm()

    paginator = Paginator(photographers.order_by('-created_at'), 10)

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
        'pageTitle': 'Marketplace',
        'pageDescription': MAIN_PAGE_DESCRIPTION
    }
    return render(request, 'marketplace/photographer/list.html', content)

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
        hire_url = reverse('marketplace.photographer_hire', kwargs={'unique_id': str(photographer.unique_id)})
        data['photographer_html_detail'] = render_to_string('marketplace/photographer/modal_detail.html', {'photographer': photographer, 'hire_url': hire_url, 'is_mine': is_mine})
    
    return JsonResponse(data)