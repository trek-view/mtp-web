# Django Packages
from django.contrib import admin

# App packages
from .models import *

############################################################################


class PhotographerAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_name', 'business_website', 'user', 'created_at')


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
