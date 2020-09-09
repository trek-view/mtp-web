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
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_name', 'business_website', 'business_email', 'type', 'user', 'created_at')

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


class ImageQualityAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description'
    )


admin.site.register(CaptureType, CaptureTypeAdmin)
admin.site.register(CaptureMethod, CaptureMethodAdmin)
admin.site.register(ImageQuality, ImageQualityAdmin)
admin.site.register(Photographer, PhotographerAdmin)
admin.site.register(PhotographerEnquire, PhotographerEnquireAdmin)

