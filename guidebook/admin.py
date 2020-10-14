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
from tags_input import admin as tags_input_admin
############################################################################

class GuidebookAdmin(tags_input_admin.TagsInputAdmin):
    list_display = (
        'name',
        'description',
        # 'category',
        'cover_image',
        'user',
        'publish_status',
        'approve_status',
        'created_at'
    )


    def get_urls(self):
        urls = super().get_urls()
        guidebook_urls = [
            path('change_status/<int:pk>/', self.view_change_status),
        ]
        return guidebook_urls + urls

    def view_change_status(self, request, pk):
        guidebook = get_object_or_404(Guidebook, pk=pk)
        if not guidebook.is_approved:
            guidebook.is_approved = True
            guidebook.is_published = True
            guidebook.save()
            
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def approve_status(self, obj):
        if not obj.is_approved:
            return format_html(
                '<a href="/mission-control/guidebook/guidebook/change_status/%s" style="color: red; ">Unapproved</a>' % str(obj.pk)
            )
        else:
            # return format_html(
            #     '<a href="/mission-control/guidebook/guidebook/change_status/%s" style="color: green; ">Published</a>' % str(obj.pk)
            # )
            return format_html('<p style="color: green;">Approved</p>')

    def publish_status(self, obj):
        if not obj.is_published:
            return format_html('<p style="color: red;">Unpublished</p>')
        else:
            # return format_html(
            #     '<a href="/mission-control/guidebook/guidebook/change_status/%s" style="color: green; ">Published</a>' % str(obj.pk)
            # )
            return format_html('<p style="color: green;">Published</p>')

    
    publish_status.short_description = 'Published'
    approve_status.short_description = 'Approved'

class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description'
    )


class POICategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description'
    )

admin.site.register(Guidebook, GuidebookAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(POICategory, POICategoryAdmin)