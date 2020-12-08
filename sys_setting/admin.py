from django.contrib import admin

# Register your models here.
# App packages
from .models import *


class BusinessTierAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'logo'
    )


admin.site.register(BusinessTier, BusinessTierAdmin)
