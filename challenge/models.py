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
from sequence.models import TransType, CameraMake

## Python Packages
import uuid
from django.urls import reverse

UserModel = get_user_model()

class Challenge(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    transport_type = models.ManyToManyField(TransType)
    camera_make = models.ManyToManyField(CameraMake)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    expected_count = models.IntegerField(null=True, blank=True)
    geometry = models.TextField(default='')
    multipolygon = models.MultiPolygonField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    zoom = models.FloatField(default=5)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)

    objects = GeoManager()

    def get_absolute_url(self):
        return reverse('challenge.challenge_detail', kwargs={'unique_id': str(self.unique_id)})

    def getShortDescription(self):
        description = self.description
        if len(description) > 50:
            return description[0:80] + '...'
        else:
            return description
