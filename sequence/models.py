## Django Packages
from django.contrib.gis.db import models
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, get_user_model, login as auth_login,
    logout as auth_logout, update_session_auth_hash,
)
from datetime import datetime
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

## Python Packages
import uuid
from lib.functions import *
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey

UserModel = get_user_model()

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(default=None, blank=True, null=True)
    is_actived = models.BooleanField(default=True)

    def __str__(self):
        return self.name

def getAllTags():
    items = Tag.objects.filter(is_actived=True)
    itemsTuple = ()
    for item in items:
        itemsTuple = itemsTuple + ((item.pk, item.name),)
    print(itemsTuple)
    return itemsTuple

class TransType(MPTTModel):
    name = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    icon = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.parent is None:
            return self.name
        else:
            return self.parent.name + ' - ' + self.name

    class MPTTMeta:
        level_attr = 'mptt_level'
        order_insertion_by = ['name']

    class Meta:
        verbose_name_plural = 'Transport Type'


def getAllCaptureType():
    items = TransType.objects.all()
    itemsTuple = ()
    for item in items:
        itemsTuple = itemsTuple + ((item.pk, item.name),)
    return itemsTuple

class Sequence(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    camera_make = models.CharField(max_length=50, default='')
    captured_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(null=True)
    seq_key = models.CharField(max_length=100)
    pano = models.BooleanField(default=False)
    user_key = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    geometry_coordinates = models.LineStringField(null=True)
    geometry_coordinates_ary = ArrayField(ArrayField(models.FloatField(default=1)), null=True)
    coordinates_cas = ArrayField(models.FloatField(default=0), null=True)
    coordinates_image = ArrayField(models.CharField(default='', max_length=100), null=True)
    is_uploaded = models.BooleanField(default=False)
    is_privated = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)

    name = models.CharField(max_length=100, default='')
    description = models.TextField(default='')
    transport_type = models.ForeignKey(TransType, on_delete=models.CASCADE, null=True)
    tag = ArrayField(models.CharField(default='0', max_length=6), null=True)

    is_mapillary = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    is_transport = models.BooleanField(default=False)

    def getImageCount(self):
        if not self.coordinates_image is None:
            return len(self.coordinates_image)
        else:
            return 0

    def getTransportType(self):
        captureType = []
        for t in self.type:
            cType = TransportType.objects.get(pk=t)
            if cType:
                captureType.append(cType.name)

        if len(captureType) > 0:
            return ', '.join(captureType)
        else:
            return ''

    def getTagStr(self):
        tags = []
        if self.tag is None:
            return ''
        for t in self.tag:
            tag = Tag.objects.get(pk=t)
            if tag and tag.is_actived:
                tags.append(tag.name)

        if len(tags) > 0:
            return ', '.join(tags)
        else:
            return ''

    def getTags(self):
        tags = []
        if self.tag is None:
            return []
        for t in self.tag:
            tag = Tag.objects.get(pk=t)
            if tag and tag.is_actived:
                tags.append(tag.name)
        return tags

    def getShortDescription(self):
        description = self.description
        if len(description) > 100:
            return description[0:100] + '...'
        else:
            return description

    def getFirstImageKey(self):
        if len(self.coordinates_image) > 0:
            return self.coordinates_image[0]
        else:
            return ''

    def getLikeCount(self):
        liked_guidebook = SequenceLike.objects.filter(sequence=self)
        if not liked_guidebook:
            return 0
        else:
            return liked_guidebook.count()

    def getDistance(self):
        all_distance = 0
        if (len(self.geometry_coordinates_ary) > 0):
            first_point = self.geometry_coordinates_ary[0]
            for i in range(len(self.geometry_coordinates_ary) - 1):
                if i == 0:
                    continue
                second_point = self.geometry_coordinates_ary[i]
                d = distance(first_point, second_point)
                first_point = second_point
                all_distance += d
            all_distance = "%.3f" % all_distance
        return all_distance

    # def getTourCount(self):
    #     tour_sequences = TourSequence.objects.filter(sequence=self)
    #     return tour_sequences.count()

class Image(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    camera_make = models.CharField(max_length=150, default='')
    camera_model = models.CharField(max_length=150, default='')
    cas = models.FloatField(default=0)
    captured_at = models.DateTimeField(null=True)
    seq_key = models.CharField(max_length=100, default='')
    image_key = models.CharField(max_length=100)
    pano = models.BooleanField(default=False)
    user_key = models.CharField(max_length=100, default='')
    username = models.CharField(max_length=100, default='')
    organization_key = models.CharField(max_length=255, null=True)
    is_uploaded = models.BooleanField(default=False)
    is_privated = models.BooleanField(default=False)
    is_mapillary = models.BooleanField(default=True)
    lat = models.FloatField(default=0)
    lng = models.FloatField(default=0)
    type = models.CharField(max_length=50, default='Point')

    def getSequence(self):
        if self.seq_key != '':
            sequence = Sequence.objects.get(seq_key=self.seq_key)
            if sequence is None or not sequence:
                return None
            return sequence
        return None

class SequenceLike(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE)
