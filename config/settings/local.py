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

DEBUG = True

INSTALLED_APPS += ['whitenoise.runserver_nostatic']



STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

GOOGLE_ANALYTICS = 'UA-111111111-1'

MAILERLITE_TOKEN = ''
MAILERLIST_API_KEY = ''
MAILERLIST_GROUP_ID = ''

MAPBOX_PUBLISH_TOKEN = ''

# Mapillary settings
MAPILLARY_AUTHENTICATION_URL = ''
MAPILLARY_CLIENT_ID = ''
MAPILLARY_CLIENT_SECRET = '='
MTP_DESKTOP_UPLOADER_CLIENT_ID = ''
MTP_DESKTOP_UPLOADER_CLIENT_SECRET = '='

SECRET_KEY = ''

EMAIL_FILE_PATH = os.path.join(BASE_DIR, "sent_emails")
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = ''
SMTP_USER = ''
EMAIL_HOST_USER = SMTP_USER
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = True
EMAIL_PORT = 587
SMTP_FROM_NAME = ''
DEFAULT_FROM_EMAIL = '%s <%s>' % (SMTP_FROM_NAME, SMTP_USER)
SMTP_REPLY_TO = ''

SITE_ID = 1

FONT_AWESOME_KIT = ''

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=100000000),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=1000000000),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'SIGNING_KEY': SECRET_KEY,
    'ALGORITHM': 'HS256',
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=100000000),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(minutes=1000000000),
}

WEATHERSTACK_API_KEY = ''

# Don't fill this option.
# Keep empty string to run this app on local
AWS_STORAGE_BUCKET_NAME = ''
