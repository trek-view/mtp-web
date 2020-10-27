from django.contrib import admin

# Register your models here.
# App packages
from .models import *


class BusinessTierAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'logo'
    )


class GoldTierAdmin(admin.ModelAdmin):
    list_display = (
        'user',
    )


class SilverTierAdmin(admin.ModelAdmin):
    list_display = (
        'user',
    )


admin.site.register(BusinessTier, BusinessTierAdmin)
admin.site.register(GoldTier, GoldTierAdmin)
admin.site.register(SilverTier, SilverTierAdmin)

