from .base import *
import dj_database_url
import django_heroku

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'default')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

INSTALLED_APPS += ['storages']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
if not os.environ.get('HEROKU_POSTGRESQL_SILVER_URL') is None:
    DATABASE_VARIABLE = 'HEROKU_POSTGRESQL_SILVER_URL'
elif not os.environ.get('HEROKU_POSTGRESQL_AQUA_URL') is None:
    DATABASE_VARIABLE = 'HEROKU_POSTGRESQL_AQUA_URL'
else:
    DATABASE_VARIABLE = 'DATABASE_URL'
DATABASES = {
    'default': dj_database_url.config(env=DATABASE_VARIABLE, ssl_require=True)
}
DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'

ROBOTS_USE_SITEMAP = False

BASE_URL = os.environ.get('BASE_URL')

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
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_S3_BUCKET")
AWS_S3_BUCKET_CNAME = os.environ.get("AWS_S3_BUCKET_CNAME")
AWS_QUERYSTRING_AUTH = False # This will make sure that the file URL does not have unnecessary parameters like your access key.
AWS_S3_CUSTOM_DOMAIN = AWS_STORAGE_BUCKET_NAME
AWS_S3_MAPILLARY_BUCKET = os.environ.get("AWS_S3_MAPILLARY_BUCKET")
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
MAPBOX_PUBLISH_TOKEN = os.environ.get('MAPBOX_TOKEN')

# Setting for mailgun
EMAIL_FILE_PATH = os.path.join(BASE_DIR, "sent_emails")
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('SMTP_HOSTNAME')
SMTP_USER = os.environ.get('SMTP_USER')
EMAIL_HOST_USER = SMTP_USER
EMAIL_HOST_PASSWORD = os.environ.get('SMTP_PASSWORD')
EMAIL_USE_TLS = True
EMAIL_PORT = 587
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME')
DEFAULT_FROM_EMAIL = '%s <%s>' % (SMTP_FROM_NAME, SMTP_USER)
SMTP_REPLY_TO = os.environ.get('SMTP_REPLY_TO')

# Settings for mailist
MAILERLIST_API_KEY = os.environ.get('MAILERLITE_TOKEN')
MAILERLIST_GROUP_ID = os.environ.get('MAILERLITE_GROUPID')

# google analysis
GOOGLE_ANALYTICS = os.environ.get('GOOGLE_ANALYTICS')

# Mapillary settings
MAPILLARY_AUTHENTICATION_URL = os.environ.get('MAPILLARY_AUTHENTICATION_URL')
MAPILLARY_CLIENT_ID = os.environ.get('MAPILLARY_CLIENT_ID')
MAPILLARY_CLIENT_SECRET = os.environ.get('MAPILLARY_CLIENT_SECRET')
MTP_DESKTOP_UPLOADER_CLIENT_ID = os.environ.get('MTP_DESKTOP_UPLOADER_CLIENT_ID')
MTP_DESKTOP_UPLOADER_CLIENT_SECRET = os.environ.get('MTP_DESKTOP_UPLOADER_CLIENT_SECRET')

#sitemap
SITE_ID = os.environ.get('SITE_ID')

FONT_AWESOME_KIT = os.environ.get('FONT_AWESOME_KIT')

WEATHERSTACK_API_KEY = os.environ.get('WEATHERSTACK_API_KEY')

