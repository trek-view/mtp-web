import tempfile

import requests
from django.conf import settings


class Mapillary:

    """
    """

    client_id = settings.MAPILLARY_CLIENT_ID
    client_secret = settings.MAPILLARY_CLIENT_SECRET
    root_url = 'https://a.mapillary.com/v3/'
    token = None
    source = None
    user_data = None

    def __init__(self, token=None, source=None):
        self.token = token
        self.source = source
        if self.source == 'mtpdu':
            self.client_id = settings.MTP_DESKTOP_UPLOADER_CLIENT_ID
            self.client_secret = settings.MTP_DESKTOP_UPLOADER_CLIENT_SECRET
        user_data = self.get_mapillary_user()
        if user_data:
            self.user_data = user_data

    @staticmethod
    def __check_response(response):
        try:
            data = response.json()
        except:
            print('Response error')
            return False
        if data is None or 'message' in data.keys():
            return False
        else:
            return data

    def get_images_by_sequence_key(self, seq_keys):
        sequence_str = ','.join(seq_keys)
        per_page = 1000
        url = '{}images?client_id={}&sequence_keys={}&per_page={}'.format(self.root_url, self.client_id, sequence_str, per_page)
        response = requests.get(url)
        data = self.__check_response(response)
        return data

    def get_images_with_ele_by_seq_key(self, seq_keys):
        sequence_str = ','.join(seq_keys)
        per_page = 1000
        url = '{}images_computed?client_id={}&sequence_keys={}&per_page={}'.format(self.root_url, self.client_id, sequence_str, per_page)
        response = requests.get(url)
        data = self.__check_response(response)
        return data

    def get_images_by_image_key(self, image_keys):
        image_str = ','.join(image_keys)
        per_page = 1000
        url = '{}images?client_id={}&image_keys={}&per_page={}'.format(self.root_url, self.client_id, image_str, per_page)
        response = requests.get(url)
        data = self.__check_response(response)
        return data

    def get_detection_by_image_key(self, image_keys, type='trafficsigns'):

        image_str = ','.join(image_keys)
        per_page = 1000
        url = '{}object_detections/{}?client_id={}&image_keys={}&per_page={}'.format(self.root_url, type, self.client_id, image_str, per_page)
        response = requests.get(url)
        data = self.__check_response(response)
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
        data = self.__check_response(response)
        return data

    def download_mapillary_image(self, image_key):
        if self.token is None:
            return False
        url = '{}images/{}/download_original?client_id={}'.format(self.root_url, image_key, self.client_id)
        headers = {"Authorization": "Bearer {}".format(self.token)}
        request = requests.get(url, headers=headers, stream=True)
        # Was the request OK?
        if request.status_code != requests.codes.ok:
            # Nope, error handling, skip file etc etc etc

            return False

        # # Get the filename from the url, used for saving later
        # file_name = image_url.split('/')[-1]

        # Create a temporary file
        lf = tempfile.NamedTemporaryFile()

        # Read the streamed image in sections
        for block in request.iter_content(1024 * 8):

            # If no more file then stop
            if not block:
                break

            # Write image block to temporary file
            lf.write(block)
        return lf

    def get_mapillary_user(self):
        if self.token is None:
            return False
        url = '{}me?client_id={}'.format(self.root_url, self.client_id)
        headers = {"Authorization": "Bearer {}".format(self.token)}
        response = requests.get(url, headers=headers)
        data = self.__check_response(response)
        return data

    def get_sequence_by_key(self, seq_key):
        if self.token is None:
            return False
        url = '{}sequences/{}?client_id={}'.format(self.root_url, seq_key, self.client_id)
        headers = {"Authorization": "Bearer {}".format(self.token)}
        response = requests.get(url, headers=headers)
        data = self.__check_response(response)
        return data

    def get_sequence(self, bbox=None, start_time=None, end_time=None, per_page=None, private=None, starred=None, tile=None, organization_keys=None, userkeys=None, usernames=None):
        params = {'client_id': self.client_id}

        if bbox is not None:
            params['bbox'] = bbox

        if start_time is not None:
            params['start_time'] = str(start_time)

        if end_time is not None:
            params['end_time'] = str(end_time)

        if per_page is not None:
            params['per_page'] = str(per_page)

        if starred is not None:
            if starred:
                params['starred'] = 'true'
            else:
                params['starred'] = 'false'

        if private is not None:
            if private:
                params['private'] = 'true'
            else:
                params['private'] = 'false'

        if tile is not None:
            params['tile'] = tile

        if organization_keys is not None:
            if isinstance(organization_keys, list):
                organization_keys = ','.join(organization_keys)
            params['organization_keys'] = organization_keys

        if userkeys is not None:
            if isinstance(userkeys, list):
                userkeys = ','.join(userkeys)
            params['userkeys'] = userkeys

        if usernames is not None:
            if isinstance(usernames, list):
                usernames = ','.join(usernames)
            params['usernames'] = usernames

        url = '{}sequences'.format(self.root_url)
        response = requests.get(url, params=params)
        data = self.__check_response(response)
        return data

    def set_token(self, token):
        self.token = token
        if token is not None:
            user_data = self.get_mapillary_user()
            if user_data:
                self.user_data = user_data

