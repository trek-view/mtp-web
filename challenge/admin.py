# Django Packages
from django.contrib import admin

# App packages
from .models import *


# Custom Libs ##


############################################################################
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')

class LabelChallengeAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')

admin.site.register(Challenge, ChallengeAdmin)
admin.site.register(LabelChallenge, LabelChallengeAdmin)

