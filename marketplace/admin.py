## Django Packages
from django.contrib import admin
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.urls import reverse
from django.urls import path
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string

## Custom Libs ##
from lib.functions import send_mail_with_html

## App packages
from .models import *

############################################################################

class JobAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'organisation_name',
        'organisation_website',
        'organisation_category',
        'app_email',
        'type',
        'user',
        'publish_status',
        'approve_status',
        'received',
        'created_at'
    )

    def get_urls(self):
        urls = super().get_urls()
        job_urls = [
            path('change_status/<int:pk>/', self.view_change_status),
        ]
        return job_urls + urls

    def view_change_status(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        if not job.is_approved:
            job.is_approved = True
            job.is_published = True
            job.save()

            # send email to job owner
            try:
                subject = 'Your job "%s" is approved.' % job.name
                html_message = render_to_string(
                    'emails/marketplace/job/approved.html', 
                    { 'subject': subject, 'job': job}, 
                    request
                )
                send_mail_with_html(subject, html_message, job.user.email)
            except:
                print('email sending error!')
            
            
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def approve_status(self, obj):
        if not obj.is_approved:
            return format_html(
                '<a href="/mission-control/marketplace/job/change_status/%s" style="color: red; ">Unapproved</a>' % str(obj.pk)
            )
        else:
            # return format_html(
            #     '<a href="/mission-control/marketplace/job/change_status/%s" style="color: green; ">Published</a>' % str(obj.pk)
            # )
            return format_html('<p style="color: green;">Approved</p>')

    def publish_status(self, obj):
        if not obj.is_published:
            return format_html('<p style="color: red;">Unpublished</p>')
        else:
            # return format_html(
            #     '<a href="/mission-control/marketplace/job/change_status/%s" style="color: green; ">Published</a>' % str(obj.pk)
            # )
            return format_html('<p style="color: green;">Published</p>')

    def received(self, obj):
        if JobApplication.objects.filter(job=obj).count() > 0:
            return format_html(
                '<img src="/static/admin/img/icon-yes.svg" alt="True">'
            )
        else:
            return format_html(
                '<img src="/static/admin/img/icon-no.svg" alt="True">'
            )

    publish_status.short_description = 'Published'
    received.short_description = 'Received'
    approve_status.short_description = 'Approved'

class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at')

class PhotographerAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_name', 'business_website', 'business_email', 'type', 'user', 'publish_status', 'approve_status', 'created_at')

    def get_urls(self):
        urls = super().get_urls()
        photographer_urls = [
            path('change_status/<int:pk>/', self.view_change_status),
        ]
        return photographer_urls + urls

    def view_change_status(self, request, pk):
        photographer = get_object_or_404(Photographer, pk=pk)
        if not photographer.is_approved:
            photographer.is_approved = True
            photographer.is_published = True
            photographer.save()

            # sending email to photographer owner
            try:
                subject = 'Your photographer "%s" is approved.' % photographer.name
                html_message = render_to_string(
                    'emails/marketplace/photographer/approved.html', 
                    { 'subject': subject, 'photographer': photographer}, 
                    request
                )
                send_mail_with_html(subject, html_message, photographer.user.email)
            except:
                print('email sending error!')

            
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def approve_status(self, obj):
        if not obj.is_approved:
            return format_html(
                '<a href="/mission-control/marketplace/photographer/change_status/%s" style="color: red; ">Unapproved</a>' % str(obj.pk)
            )
        else:
            # return format_html(
            #     '<a href="/admin/marketplace/job/change_status/%s" style="color: green; ">Published</a>' % str(obj.pk)
            # )
            return format_html('<p style="color: green;">Approved</p>')

    def publish_status(self, obj):
        if not obj.is_published:
            return format_html('<p style="color: red;">Unpublished</p>')
        else:
            return format_html('<p style="color: green;">Published</p>')
            # return format_html(
            #     '<a href="/admin/marketplace/photographer/change_status/%s" style="color: green; ">Published</a>' % str(obj.pk)
            # )

    publish_status.short_description = 'Published'
    approve_status.short_description = 'Approved'

class PhotographerEnquireAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at')

class CaptureTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description'
    )

class CaptureMethodAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description'
    )

class OrganisationCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description'
    )

class ImageQualityAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description'
    )

admin.site.register(CaptureType, CaptureTypeAdmin)
admin.site.register(CaptureMethod, CaptureMethodAdmin)
admin.site.register(OrganisationCategory, OrganisationCategoryAdmin)
admin.site.register(ImageQuality, ImageQualityAdmin)

admin.site.register(Job, JobAdmin)
admin.site.register(JobApplication, JobApplicationAdmin)
admin.site.register(Photographer, PhotographerAdmin)
admin.site.register(PhotographerEnquire, PhotographerEnquireAdmin)

