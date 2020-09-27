## Django Packages
from django.contrib.gis.db import models
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, get_user_model, login as auth_login,
    logout as auth_logout, update_session_auth_hash,
)
from django.db.models import Manager as GeoManager
from datetime import datetime
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

## Python Packages
import uuid
from django.urls import reverse

UserModel = get_user_model()


class CaptureType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(default=None, blank=True, null=True)
    def __str__(self):
        return self.name

class CaptureMethod(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(default=None, blank=True, null=True)
    def __str__(self):
        return self.name

class ImageQuality(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(default=None, blank=True, null=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = 'Image Quality'


def getAllCaptureType():
    items = CaptureType.objects.all()
    itemsTuple = ()
    for item in items:
        itemsTuple = itemsTuple + ((item.pk, item.name),)
    return itemsTuple


def getAllCaptureMethod():
    items = CaptureMethod.objects.all()
    itemsTuple = ()
    for item in items:
        itemsTuple = itemsTuple + ((item.pk, item.name),)
    return itemsTuple


def getAllImageQuality():
    items = ImageQuality.objects.all()
    itemsTuple = ()
    for item in items:
        itemsTuple = itemsTuple + ((item.pk, item.name),)
    return itemsTuple



class Photographer(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    business_name = models.CharField(max_length=200)
    business_website = models.TextField()
    description = models.TextField()
    capture_type = models.ManyToManyField(CaptureType)
    capture_method = models.ManyToManyField(CaptureMethod)
    image_quality = models.ForeignKey(ImageQuality, on_delete=models.CASCADE, null=True, blank=True)
    geometry = models.TextField(default='')
    multipolygon = models.MultiPolygonField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    zoom = models.FloatField(default=5)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)

    objects = GeoManager()

    def get_absolute_url(self):
        return reverse('photographer.photographer_detail', kwargs={'unique_id': str(self.unique_id)})

    def getShortDescription(self):
        description = self.description
        if len(description) > 50:
            return description[0:80] + '...'
        else:
            return description

    def getCaptureType(self):
        captureType = []
        for cType in self.capture_type.all():
            if cType:
                captureType.append(cType.name)

        if len(captureType) > 0:
            return ', '.join(captureType)
        else:
            return ''

    def getCaptureMethod(self):
        captureMethod = []
        for cMethod in self.capture_method.all():
            if cMethod:
                captureMethod.append(cMethod.name)
        if len(captureMethod) > 0:
            return ', '.join(captureMethod)
        else:
            return ''

    def getImageQuality(self):
        image_quality = ImageQuality.objects.get(pk=self.image_quality)
        if image_quality:
            return image_quality.name
        else:
            return ''


class PhotographerEnquire(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    photographer = models.ForeignKey(Photographer, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    email = models.CharField(max_length=200)
    # phone = models.CharField(max_length=20)
    # website = models.TextField(default=None, blank=True, null=True)
    description = models.TextField(default=None, blank=True, null=True)
    status = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
