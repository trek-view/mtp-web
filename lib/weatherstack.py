from django.core.mail.message import EmailMultiAlternatives
from django.conf import settings
from django.http import (
    Http404, HttpResponse, JsonResponse, HttpResponsePermanentRedirect, HttpResponseRedirect,
)
import time
import requests
import math
import tempfile


class Weatherstack():
    access_key = settings.WEATHERSTACK_API_KEY
    root_url = 'http://api.weatherstack.com/'

    def get_historical_data(self, point, historical_date):
        params = {
            'access_key': self.access_key,
            'query': str(point[0]) + ',' + str(point[1]),
            'historical_date': historical_date,
            'hourly': '1'
        }

        api_result = requests.get(self.root_url + 'historical', params)

        try:
            data = api_result.json()
        except:
            print('Response error')
            return False
        if data is None or ('success' in data.keys() and not data['success']):
            print(data['error'])
            return False
        else:
            return data