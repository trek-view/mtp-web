import tempfile

import requests
from django.conf import settings


class Mapillary:
    client_id = settings.MAPILLARY_CLIENT_ID
    client_secret = settings.MAPILLARY_CLIENT_SECRET
    root_url = 'https://a.mapillary.com/v3/'
    token = None
    source = None
    mapillary_user_data = None

    def __init__(self, token=None, source=None):
        self.token = token
        self.source = source
        if self.source == 'mtpdu':
            self.client_id = settings.MTP_DESKTOP_UPLOADER_CLIENT_ID
            self.client_secret = settings.MTP_DESKTOP_UPLOADER_CLIENT_SECRET

    def get_images_by_sequence_key(self, seq_keys):
        sequence_str = ','.join(seq_keys)
        per_page = 1000
        url = '{}images?client_id={}&sequence_keys={}&per_page={}'.format(self.root_url, self.client_id, sequence_str, per_page)
        response = requests.get(url)
        try:
            data = response.json()
        except:
            print('Response error')
            return False
        if data is None or 'message' in data.keys():
            return False
        else:
            return data

    def get_images_with_ele_by_seq_key(self, seq_keys):
        sequence_str = ','.join(seq_keys)
        per_page = 1000
        url = '{}images_computed?client_id={}&sequence_keys={}&per_page={}'.format(self.root_url, self.client_id, sequence_str, per_page)
        response = requests.get(url)
        try:
            data = response.json()
        except:
            print('Response error')
            return False
        if data is None or 'message' in data.keys():
            return False
        else:
            return data

    def get_images_by_image_key(self, image_keys):
        image_str = ','.join(image_keys)
        per_page = 1000
        url = '{}images?client_id={}&image_keys={}&per_page={}'.format(self.root_url, self.client_id, image_str, per_page)
        response = requests.get(url)
        try:
            data = response.json()
        except:
            print('Response error')
            return False
        if data is None or 'message' in data.keys():
            return False
        else:
            return data

    def get_detection_by_image_key(self, image_keys, type='trafficsigns'):

        image_str = ','.join(image_keys)
        per_page = 1000
        url = '{}object_detections/{}?client_id={}&image_keys={}&per_page={}'.format(self.root_url, type, self.client_id, image_str, per_page)
        response = requests.get(url)
        print(response)
        try:
            data = response.json()
        except:
            print('Response error')
            return False

        if data is None or 'message' in data.keys():
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
        try:
            data = response.json()
        except:
            print('Response error')
            return False
        if data is None or 'message' in data.keys():
            return False
        else:
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
        try:
            data = response.json()
        except:
            print('Response error')
            return False
        if data is None or 'message' in data.keys():
            return False
        else:
            return data

    def get_sequence_by_key(self, seq_key):
        if self.token is None:
            return False
        url = '{}sequences/{}?client_id={}'.format(self.root_url, seq_key, self.client_id)
        headers = {"Authorization": "Bearer {}".format(self.token)}
        response = requests.get(url, headers=headers)
        try:
            data = response.json()
        except:
            print('Response error')
            return False
        if data is None or 'message' in data.keys():
            return False
        else:
            self.mapillary_user_data = data
            return data