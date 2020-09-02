## Python packages
from datetime import datetime
import json
import re
from binascii import a2b_base64
import os

## Django Packages
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.http import (
    Http404, HttpResponse, JsonResponse, HttpResponsePermanentRedirect, HttpResponseRedirect,
)
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.contrib.gis.geos import Point
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

## Custom Libs ##
from lib.functions import *

## Project packages
from accounts.models import CustomUser

## App packages

# That includes from .models import *

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from sequence.models import Sequence, TransType, Tag as SeqTag

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sequence_import(request):
    feature = request.POST.get('mapillary_data')
    feature = json.loads(feature)
    properties = feature['properties']
    geometry = feature['geometry']
    seq_key = properties['key']
    sequences = Sequence.objects.filter(seq_key=seq_key)[:1]
    if sequences.count() == 0:
        sequence = Sequence()
    else:
        sequence = sequences[0]
    sequence.user = request.user
    if 'camera_make' in properties:
        sequence.camera_make = properties['camera_make']
    sequence.captured_at = properties['captured_at']
    if 'created_at' in properties:
        sequence.created_at = properties['created_at']
    sequence.seq_key = properties['key']
    if 'pano' in properties:
        sequence.pano = properties['pano']
    if 'user_key' in properties:
        sequence.user_key = properties['user_key']
    if 'username' in properties:
        sequence.username = properties['username']
    sequence.geometry_coordinates_ary = geometry['coordinates']
    sequence.image_count = len(geometry['coordinates'])
    sequence.coordinates_cas = properties['coordinateProperties']['cas']
    sequence.coordinates_image = properties['coordinateProperties']['image_keys']
    if 'private' in properties:
        sequence.is_privated = properties['private']


    sequence.name = request.POST.get('name')
    sequence.description = request.POST.get('description')
    sequence.transport_type_id = request.POST.get('transport_type')
    sequence.is_published = True
    sequence.save()

    tags = request.POST.get('tag')
    tag_ary = tags.split(',')
    if len(tag_ary) > 0:
        for t in tag_ary:
            tag = SeqTag.objects.filter(name__iexact=t)[:1]
            if tag.count() > 0:
                seq_tag = tag[0]
            else:
                seq_tag = SeqTag()
                seq_tag.name = t
                seq_tag.save()
            sequence.tag.add(seq_tag)

        for tag in sequence.tag.all():
            if not tag.name in tag_ary:
                sequence.tag.remove(tag)

    return JsonResponse({
        'status': 'success',
        'message': 'Sequence successfully imported.',
        'unique_id': str(sequence.unique_id)
    })

