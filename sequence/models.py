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
from django.urls import reverse


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

class TransportType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(default='')

    def __str__(self):
        return self.name

def getAllCaptureType():
    items = TransportType.objects.all()
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
    transport_type = models.ForeignKey(TransportType, on_delete=models.CASCADE, null=True)
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

class TourTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(default=None, blank=True, null=True)
    is_actived = models.BooleanField(default=True)

    def __str__(self):
        return self.name

def getAllTourTags():
    items = TourTag.objects.filter(is_actived=True)
    itemsTuple = ()
    for item in items:
        itemsTuple = itemsTuple + ((item.pk, item.name),)
    print(itemsTuple)
    return itemsTuple


class Tour(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    tag = ArrayField(models.CharField(default='0', max_length=6), null=True)
    name = models.CharField(max_length=100, default='')
    username = models.CharField(max_length=100, null=True)
    description = models.TextField(default='')
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    is_published = models.BooleanField(default=False)

    def getTagStr(self):
        tags = []
        if self.tag is None:
            return ''
        for t in self.tag:
            tag = TourTag.objects.get(pk=t)
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
            tag = TourTag.objects.get(pk=t)
            if tag and tag.is_actived:
                tags.append(tag.name)
        return tags

    def getShortDescription(self):
        description = self.description
        if len(description) > 100:
            return description[0:100] + '...'
        else:
            return description

    def geometrySequence(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        geometry = []

        if tour_sequences.count() > 0:
            for t_s in tour_sequences:
                sequence = t_s.sequence
                first_image = sequence.geometry_coordinates_ary[0]
                geometry.append(first_image)

        return geometry

    def getImageCount(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        image_count = 0
        if tour_sequences.count() > 0:
            for tour_sequence in tour_sequences:
                sequence = tour_sequence.sequence
                image_count += sequence.getImageCount()

        return image_count

    def getLikeCount(self):
        liked_guidebook = TourLike.objects.filter(tour=self)
        if not liked_guidebook:
            return 0
        else:
            return liked_guidebook.count()

    def getSequenceCount(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        return tour_sequences.count()

class TourSequence(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE)
    sort = models.IntegerField(default=1)

class SequenceLike(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE)

class TourLike(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)

