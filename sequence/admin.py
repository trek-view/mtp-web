# Django Packages
from django.contrib import admin
from django.utils.html import mark_safe
from tags_input import admin as tags_input_admin

# App packages
from .models import *

############################################################################


class TransTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'parent',
        'icon',
        'description'
    )


class LabelTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'parent',
        'description',
        'label_color',
        'source'
    )

    def label_color(self, obj):
        if obj.color is None:
            return ''
        return mark_safe('<span style="color: '+obj.color+'">'+obj.color+'</span>')

    label_color.short_description = 'color'


class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description'
    )


class SequenceAdmin(tags_input_admin.TagsInputAdmin):
    list_display = (
        'unique_id',
        'name',
        'description',
        'camera_make',
        'mapillary_sequence_key',
        'mapillary_user_key',
        'mapillary_username',
        'pano',
        'name',
        'description'
    )

    def mapillary_sequence_key(self, obj):
        return obj.seq_key

    def mapillary_user_key(self, obj):
        return obj.user_key

    def mapillary_username(self, obj):
        return obj.username

    mapillary_sequence_key.short_description = 'Mapillary Sequence Key'
    mapillary_user_key.short_description = 'Mapillary User Key'
    mapillary_username.short_description = 'Mapillary Username'

    # def get_queryset(self, request):
    #     query = super(SequenceAdmin, self).get_queryset(request)
    #     filtered_query = query.filter(is_transport=True)
    #     return filtered_query


class IconAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'font_awesome',
    )


class ImageAdmin(admin.ModelAdmin):
    list_display = (
        'image_key',
    )


class CameraMakeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )


class CameraModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )


admin.site.register(TransType, TransTypeAdmin)
admin.site.register(LabelType, LabelTypeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Sequence, SequenceAdmin)
admin.site.register(Icon, IconAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(CameraMake, CameraMakeAdmin)
admin.site.register(CameraModel, CameraModelAdmin)
