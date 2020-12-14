from .base import *
import os
if os.name == 'nt':
    import platform
    OSGEO4W = r"C:\OSGeo4W"


    # if '64' in platform.architecture()[0]:
    #     OSGEO4W += "64"
    assert os.path.isdir(OSGEO4W), "Directory does not exist: " + OSGEO4W
    os.environ['OSGEO4W_ROOT'] = OSGEO4W
    os.environ['GDAL_DATA'] = OSGEO4W + r"\share\gdal"
    os.environ['PROJ_LIB'] = OSGEO4W + r"\share\proj"
    os.environ['PATH'] = OSGEO4W + r"\bin;" + os.environ['PATH']

# import dj_database_url
from decouple import config

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', 'default')
# SECURITY WARNING: don't run with debug turned on in production!
debug = config('DEBUG', '0')
if debug == '1':
    DEBUG = True
else:
    DEBUG = False


INSTALLED_APPS += ['whitenoise.runserver_nostatic']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True


DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': '5432'
    }
}

ROBOTS_USE_SITEMAP = False

BASE_URL = config('BASE_URL')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)s [%(process)d] [%(levelname)s] ' +
                       'pathname=%(pathname)s lineno=%(lineno)s ' +
                       'funcname=%(funcName)s %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'testlogger': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}

# Set S3 as the place to store your files.
DEFAULT_FILE_STORAGE = "config.settings.storage_backends.MediaStorage"
STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = config("AWS_S3_BUCKET")
AWS_S3_BUCKET_CNAME = config("AWS_S3_BUCKET_CNAME")
AWS_QUERYSTRING_AUTH = False # This will make sure that the file URL does not have unnecessary parameters like your access key.
AWS_S3_CUSTOM_DOMAIN = AWS_STORAGE_BUCKET_NAME
AWS_S3_MAPILLARY_BUCKET = config("AWS_S3_MAPILLARY_BUCKET")
# Static media settings
STATIC_URL = 'https://' + AWS_STORAGE_BUCKET_NAME + '/'
MEDIA_URL = 'https://' + AWS_S3_MAPILLARY_BUCKET + '/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"), )
STATIC_ROOT = 'staticfiles'
MEDIA_ROOT = 'media'
ADMIN_MEDIA_PREFIX = MEDIA_URL + 'admin/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


# mapbox
MAPBOX_PUBLISH_TOKEN = config('MAPBOX_PUBLISH_TOKEN')
MAPBOX_ACCESS_TOKEN = config('MAPBOX_ACCESS_TOKEN')

# Setting for mailgun
EMAIL_FILE_PATH = os.path.join(BASE_DIR, "sent_emails")
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('SMTP_HOSTNAME')
SMTP_USER = config('SMTP_USER')
EMAIL_HOST_USER = SMTP_USER
EMAIL_HOST_PASSWORD = config('SMTP_PASSWORD')
EMAIL_USE_TLS = True
EMAIL_PORT = 587
SMTP_FROM_NAME = config('SMTP_FROM_NAME')
DEFAULT_FROM_EMAIL = '%s <%s>' % (SMTP_FROM_NAME, SMTP_USER)
SMTP_REPLY_TO = config('SMTP_REPLY_TO')

# Settings for mailist
MAILERLIST_API_KEY = config('MAILERLITE_TOKEN')
MAILERLIST_GROUP_ID = config('MAILERLITE_GROUPID')

# google analysis
GOOGLE_ANALYTICS = config('GOOGLE_ANALYTICS')

# Mapillary settings
MAPILLARY_AUTHENTICATION_URL = config('MAPILLARY_AUTHENTICATION_URL')
MAPILLARY_CLIENT_ID = config('MAPILLARY_CLIENT_ID')
MAPILLARY_CLIENT_SECRET = config('MAPILLARY_CLIENT_SECRET')
MTP_DESKTOP_UPLOADER_CLIENT_ID = config('MTP_DESKTOP_UPLOADER_CLIENT_ID')
MTP_DESKTOP_UPLOADER_CLIENT_SECRET = config('MTP_DESKTOP_UPLOADER_CLIENT_SECRET')

#sitemap
SITE_ID = config('SITE_ID')

FONT_AWESOME_KIT = config('FONT_AWESOME_KIT')

WEATHERSTACK_API_KEY = config('WEATHERSTACK_API_KEY')
OPENROUTESERVICE_API_KEY = config('OPENROUTESERVICE_API_KEY')

USE_TWO_FACTOR_OAUTH = config('USE_TWO_FACTOR_OAUTH')
