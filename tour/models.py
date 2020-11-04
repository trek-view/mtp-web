# Django Packages
## Python Packages
import uuid
from datetime import datetime

from django.contrib.auth import (
    get_user_model, )
from django.contrib.gis.db import models

from sequence.models import Sequence
from sys_setting.models import Tag as TourTag

UserModel = get_user_model()

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

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tour.tour_detail', kwargs={'unique_id': str(self.unique_id)})

    def get_tag_str(self):
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

    def get_tags(self):
        tags = []
        if self.tour_tag is None:
            return []
        for tag in self.tour_tag.all():
            if tag and tag.is_actived:
                tags.append(tag.name)
        return tags

    def get_short_description(self):
        description = self.description
        if len(description) > 100:
            return description[0:100] + '...'
        else:
            return description

    def geometry_sequence(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        geometry = []

        if tour_sequences.count() > 0:
            for t_s in tour_sequences:
                sequence = t_s.sequence
                first_image = sequence.geometry_coordinates_ary[0]
                geometry.append(first_image)

        return geometry

    def get_first_sequence_captured(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        if tour_sequences.count() > 0:
            return tour_sequences[0].sequence.captured_at
        else:
            return ''

    def get_first_sequence_created(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        if tour_sequences.count() > 0:
            return tour_sequences[0].sequence.created_at
        else:
            return ''

    def get_image_count(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        image_count = 0
        if tour_sequences.count() > 0:
            for tour_sequence in tour_sequences:
                sequence = tour_sequence.sequence
                image_count += sequence.get_image_count()

        return image_count

    def get_like_count(self):
        liked_tour = TourLike.objects.filter(tour=self)
        if not liked_tour:
            return 0
        else:
            return liked_tour.count()

    def getSequenceCount(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        return tour_sequences.count()

    def get_distance(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        distance = 0
        if tour_sequences.count() > 0:
            for t_s in tour_sequences:
                distance += float(t_s.sequence.get_distance())

        return "%.3f" % distance

    def get_cover_image(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        if tour_sequences.count() > 0:
            sequence = tour_sequences[0].sequence
            return sequence.get_cover_image()
        else:
            return None

    def get_cover_imageUserOnMapillary(self):
        tour_sequences = TourSequence.objects.filter(tour=self)
        if tour_sequences.count() > 0:
            sequence = tour_sequences[0].sequence
            return sequence.username
        else:
            return ''


class TourSequence(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE)
    sort = models.IntegerField(default=1)


class TourLike(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
