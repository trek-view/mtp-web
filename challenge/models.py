import uuid
from datetime import datetime

from django.contrib.auth import (
    get_user_model, )
from django.contrib.gis.db import models
from django.db.models import Manager as GeoManager
from django.urls import reverse

from sequence.models import TransType, CameraMake, LabelType

UserModel = get_user_model()


class Challenge(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    transport_type = models.ForeignKey(TransType, on_delete=models.CASCADE, null=True, blank=True)
    camera_make = models.ManyToManyField(CameraMake)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    geometry = models.TextField(default='')
    multipolygon = models.MultiPolygonField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    zoom = models.FloatField(default=5)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)

    objects = GeoManager()

    def get_absolute_url(self):
        return reverse('challenge.challenge_detail', kwargs={'unique_id': str(self.unique_id)})

    def get_short_description(self):
        description = self.description
        if len(description) > 50:
            return description[0:80] + '...'
        else:
            return description

    def getTrasTypes(self):
        transport_type = self.transport_type
        t = []
        if transport_type is not None:
            t.append(transport_type.getFullName())

        return ', '.join(t)

    def get_transport_types_obj(self):
        transport_types = self.transport_type.all()
        return transport_types

    def get_camera_make(self):
        camera_makes = self.camera_make.all()
        t = []
        if camera_makes.count() > 0:
            for camera_make in camera_makes:
                t.append(camera_make.name)

        return ', '.join(t)


class LabelChallenge(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    label_type = models.ManyToManyField(LabelType)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    geometry = models.TextField(default='')
    multipolygon = models.MultiPolygonField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    zoom = models.FloatField(default=5)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)

    objects = GeoManager()

    def get_absolute_url(self):
        return reverse('label_challenge.challenge_detail', kwargs={'unique_id': str(self.unique_id)})

    def get_short_description(self):
        description = self.description
        if len(description) > 50:
            return description[0:80] + '...'
        else:
            return description

    def get_label_type_obj(self):
        label_types = self.label_type.all()
        return label_types
