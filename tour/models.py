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
from django.core.validators import RegexValidator
from sequence.models import Sequence
from sequence.models import Tag as TourTag

UserModel = get_user_model()

# class TourTag(models.Model):
#     alphanumeric = RegexValidator(r'^[0-9a-zA-Z-]*$', 'Only alphanumeric characters are allowed for Username.')
#     name = models.CharField(max_length=50, unique=True, null=True, validators=[alphanumeric])
#     description = models.TextField(default=None, blank=True, null=True)
#     is_actived = models.BooleanField(default=True)
#
#     def __str__(self):
#         return self.name

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
    tour_tag = models.ManyToManyField(TourTag)
    name = models.CharField(max_length=100, default='')
    username = models.CharField(max_length=100, null=True)
    description = models.TextField(default='')
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    is_published = models.BooleanField(default=True)

    def getTagStr(self):
        tags = []
        if self.tour_tag is None:
            return ''
        for tag in self.tour_tag.all():
            if tag and tag.is_actived:
                tags.append(tag.name)

        if len(tags) > 0:
            return ', '.join(tags)
        else:
            return ''

    def getTags(self):
        tags = []
        if self.tour_tag is None:
            return []
        for tag in self.tour_tag.all():
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

    def getFirstSequenceCaptured(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        if tour_sequences.count() > 0:
            return tour_sequences[0].sequence.captured_at
        else:
            return ''

    def getFirstSequenceCreated(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        if tour_sequences.count() > 0:
            return tour_sequences[0].sequence.created_at
        else:
            return ''

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

    def getDistance(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        distance = 0
        if tour_sequences.count() > 0:
            for t_s in tour_sequences:
                distance += float(t_s.sequence.getDistance())

        return "%.3f" % distance

    def getCoverImage(self):

        tour_sequences = TourSequence.objects.filter(tour=self)
        if tour_sequences.count() > 0:
            sequence = tour_sequences[0].sequence
            return sequence.getCoverImage()
        else:
            return None


class TourSequence(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE)
    sort = models.IntegerField(default=1)

class TourLike(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
