import os
import dj_database_url
import django_heroku

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY','default')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django_email_verification',
    'accounts.apps.AccountsConfig',
    'marketplace.apps.MapPathsConfig',
    'guidebook.apps.GuidebookConfig',
    'sequence.apps.SequenceConfig',
    'lib.apps.LibConfig',
    # 'oauth2_provider',
    # 'corsheaders',
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',
    'storages',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django_cleanup.apps.CleanupConfig',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'accounts.AuthenticateMiddleware.AuthMd',
    'django_otp.middleware.OTPMiddleware',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True

TWO_FACTOR_PATCH_ADMIN = True
TWO_FACTOR_CALL_GATEWAY = None

TWO_FACTOR_SMS_GATEWAY = None
LOGIN_URL = 'two_factor:login'
# LOGIN_REDIRECT_URL = 'two_factor:profile'
CORS_ORIGIN_ALLOW_ALL = True
TWO_FACTOR_TOTP_DIGITS = 6


ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # 'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.get_settings',
                'config.context_processors.baseurl',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

LOGIN_REQUIRED_URLS = (
        r'/accounts/(.*)$',
        r'/',
    )
LOGIN_REQUIRED_URLS_EXCEPTIONS = (
    r'/accounts/login(.*)$',
    r'/accounts/logout(.*)$',
    r'/accounts/signup(.*)$',
    r'/accounts/password_reset(.*)$',
    r'/accounts/password_reset/done(.*)$',
    r'/accounts/reset/(.*)$',
    r'/accounts/reset/done(.*)$',
    r'/admin/(.*)$',
)

AUTH_USER_MODEL = 'accounts.CustomUser'

DEBUG_PROPAGATE_EXCEPTIONS = True


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}

ROBOTS_USE_SITEMAP = False

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
# settings to deply static folder in production mode on heroku
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# STATIC_URL = '/static/'
# STATICFILES_DIRS = (
#     os.path.join(BASE_DIR, 'static'),
# )

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'staticfiles/media')

# Set S3 as the place to store your files.
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_S3_BUCKET")
AWS_QUERYSTRING_AUTH = False # This will make sure that the file URL does not have unnecessary parameters like your access key.
AWS_S3_CUSTOM_DOMAIN = AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com'

# Static media settings
STATIC_URL = 'https://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/'
MEDIA_URL = STATIC_URL + 'media/'
STATICFILES_DIRS = ( os.path.join(BASE_DIR, "static"), )
STATIC_ROOT = 'staticfiles'
MEDIA_ROOT = 'media'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
AWS_DEFAULT_ACL = None



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

#sitemap
SITE_ID = os.environ.get('SITE_ID')



