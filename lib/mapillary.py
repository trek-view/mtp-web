from django.core.mail.message import EmailMultiAlternatives
from django.conf import settings
from django.http import (
    Http404, HttpResponse, JsonResponse, HttpResponsePermanentRedirect, HttpResponseRedirect,
)
import time
import requests
import math

class Mapillary():
    client_id = settings.MAPILLARY_CLIENT_ID
    client_secret = settings.MAPILLARY_CLIENT_SECRET
    root_url = 'https://a.mapillary.com/v3/'


    def get_images_by_sequence_key(self, seq_keys):
        sequence_str = ','.join(seq_keys)
        per_page = 1000
        url = '{}images?client_id={}&sequence_keys={}&per_page={}'.format(self.root_url, self.client_id, sequence_str, per_page)
        response = requests.get(url)
        data = response.json()
        if data is None or 'message' in data.keys():
            print(data['message'])
            return False
        else:
            return data

    def get_images_with_ele_by_seq_key(self, seq_keys):
        sequence_str = ','.join(seq_keys)
        per_page = 1000
        url = '{}images_computed?client_id={}&sequence_keys={}&per_page={}'.format(self.root_url, self.client_id, sequence_str,
                                                                          per_page)
        response = requests.get(url)
        data = response.json()
        if data is None or 'message' in data.keys():
            print(data['message'])
            return False
        else:
            return data

    def get_images_by_image_key(self, image_keys):
        image_str = ','.join(image_keys)
        per_page = 1000
        url = '{}images?client_id={}&image_keys={}&per_page={}'.format(self.root_url, self.client_id, image_str, per_page)
        response = requests.get(url)
        data = response.json()
        if data is None or 'message' in data.keys():
            print(data['message'])
            return False
        else:
            return data

    def get_detection_by_image_key(self, image_keys, type='trafficsigns'):

        image_str = ','.join(image_keys)
        per_page = 1000
        url = '{}object_detections/{}?client_id={}&image_keys={}&per_page={}'.format(self.root_url, type, self.client_id, image_str, per_page)
        response = requests.get(url)
        print(response)
        data = response.json()

        if data is None or 'message' in data.keys():
            print(data['message'])
            return False
        else:
            return data

    def get_map_feature_by_close_to(self, close_to, layers=None):
        if layers is None:
            layers = ['points', 'trafficsigns', 'lines']
        layers_str = ','.join(layers)
        close_str_ary = []
        for c in close_to:
            close_str_ary.append(str(c))
        close_to_str = ','.join(close_str_ary)
        per_page = 1000
        url = '{}map_features?client_id={}&closeto={}&layers={}&per_page={}'.format(self.root_url, self.client_id, close_to_str, layers_str, per_page)
        response = requests.get(url)
        data = response.json()
        if data is None or 'message' in data.keys():
            print(data['message'])
            return False
        else:
            return data