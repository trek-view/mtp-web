# Python Packages
import uuid
from datetime import datetime

# Django Packages
from django.contrib.auth import (
    get_user_model, )
from django.contrib.gis.db import models
from django.db.models import Manager as GeoManager
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


class Photographer(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    business_name = models.CharField(max_length=200)
    business_website = models.TextField()
    description = models.TextField()
    capture_type = models.ManyToManyField(CaptureType)
    capture_method = models.ManyToManyField(CaptureMethod)
    image_quality = models.ManyToManyField(ImageQuality)
    geometry = models.TextField(default='')
    multipolygon = models.MultiPolygonField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    zoom = models.FloatField(default=5)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)

    objects = GeoManager()

    def get_absolute_url(self):
        return reverse('photographer.photographer_detail', kwargs={'unique_id': str(self.unique_id)})

    def get_short_description(self):
        description = self.description
        if len(description) > 50:
            return description[0:80] + '...'
        else:
            return description

    def get_capture_type(self):
        captureType = []
        for cType in self.capture_type.all():
            if cType:
                captureType.append(cType.name)

        if len(captureType) > 0:
            return ', '.join(captureType)
        else:
            return ''

    def get_capture_method(self):
        captureMethod = []
        for cMethod in self.capture_method.all():
            if cMethod:
                captureMethod.append(cMethod.name)
        if len(captureMethod) > 0:
            return ', '.join(captureMethod)
        else:
            return ''

    def get_image_quality(self):
        imageQuality = []
        for iQuality in self.image_quality.all():
            if iQuality:
                imageQuality.append(iQuality.name)
        if len(imageQuality) > 0:
            return ', '.join(imageQuality)
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
