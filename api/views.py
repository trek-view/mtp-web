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
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from accounts.models import MapillaryUser

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

class SequenceImport(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [IsAuthenticated]
    def post(self, request, version='v1'):
        map_user_data = check_mapillary_token(request.user)
        if not map_user_data:
            return Response({'error': 'Mapillary token is invalid', 'status': False})

        seq_key = request.POST.get('sequence_key')
        if not seq_key or seq_key is None:
            return Response({'error': 'Sequence key is missing', 'status': False})
        sequence_name = request.POST.get('name')
        if not sequence_name or sequence_name is None:
            return Response({'error': 'Sequence Name is missing', 'status': False})

        sequence_json = get_sequence_by_key(request.user.mapillary_access_token, seq_key)
        if not sequence_json:
            return Response({'error': 'Sequence is empty', 'status': False})

        transport_type = request.POST.get('transport_type')
        trans_types = TransType.objects.filter(name__iexact=transport_type.lower())[:1]
        if trans_types.count() == 0:
            return Response({'error': 'Transport type is invalid', 'status': False})
        else:
            trans_type = trans_types[0]

        properties = sequence_json['properties']
        geometry = sequence_json['geometry']
        seq_key = properties['key']

        if properties['username'] != map_user_data['username']:
            return Response({'error': 'You are not owner of this sequence', 'status': False})

        sequences = Sequence.objects.filter(seq_key=seq_key)[:1]
        if sequences.count() == 0:
            sequence = Sequence()
            action = 'imported'
        else:
            sequence = sequences[0]
            action = 'updated'
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


        sequence.name = sequence_name
        if not request.POST.get('description') is None:
            sequence.description = request.POST.get('description')
        sequence.transport_type_id = trans_type.pk
        sequence.is_published = True
        sequence.is_mapillary = False
        sequence.save()

        if not request.POST.get('tag'):
            tags = request.POST.get('tag')
            tag_ary = tags.split(',')
            if len(tag_ary) > 0:
                for t in tag_ary:
                    tag = SeqTag.objects.filter(name__iexact=t.lower())[:1]
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
            'message': 'Sequence successfully was {}.'.format(action),
            'unique_id': str(sequence.unique_id)
        })

class MapillaryTokenVerify(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [IsAuthenticated]

    def post(self, request, version='v1'):
        mapillary_access_token = request.POST.get('mapillary_token')
        if mapillary_access_token is None or mapillary_access_token == '':
            return Response({'error': 'Mapillary token is invalid', 'status': False})
        user = request.user
        user.mapillary_access_token = mapillary_access_token
        user.save()

        map_user_data = check_mapillary_token(user)

        if not map_user_data:
            return Response({'error': 'Mapillary token is invalid', 'status': False})

        data = MapillaryUser.objects.filter(key=map_user_data['key'], user=request.user)
        if data.count() == 0:
            map_user = MapillaryUser()
        else:
            map_user = data[0]

        if 'about' in map_user_data:
            map_user.about = map_user_data['about']
        if 'avatar' in map_user_data:
            map_user.avatar = map_user_data['avatar']
        if 'created_at' in map_user_data:
            map_user.created_at = map_user_data['created_at']
        if 'email' in map_user_data:
            map_user.email = map_user_data['email']
        if 'key' in map_user_data:
            map_user.key = map_user_data['key']
        if 'username' in map_user_data:
            map_user.username = map_user_data['username']

        map_user.user = request.user
        map_user.save()
        return Response({'status': True, 'map_user_data': map_user_data})
