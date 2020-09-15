# storage_backends.py
from storages.backends.s3boto3 import S3Boto3Storage
import os

class MediaStorage(S3Boto3Storage):
    bucket_name = os.environ.get("AWS_S3_MAPILLARY_BUCKET")
    file_overwrite = False
    querystring_auth = False
    default_acl = None