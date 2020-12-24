## Django Packages
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

## App Packages
from .models import CustomUser, MapillaryUser, Grade


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_staff', 'date_joined', 'is_active', 'is_maillist')
    list_filter = ('email', 'username', 'is_staff', 'date_joined', 'is_active', 'is_maillist')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('user_permissions',)}),
        ('Others', {'fields': ('user_grade', 'is_staff', 'is_active', 'mapillary_access_token')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active', 'mapillary_access_token')}
        ),
    )
    search_fields = ('username',)
    ordering = ('username',)


class MapillaryUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'username', 'key', 'email', 'iamges_total_count', 'sequences_total_count', 'updated_at')


class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'sequence_limit_count')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(MapillaryUser, MapillaryUserAdmin)
admin.site.register(Grade, GradeAdmin)
