import os
import datetime
from django.conf import global_settings
from datetime import timedelta
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    # ========================
    # custom apps
    'accounts.apps.AccountsConfig',
    'photographer.apps.PhotographerConfig',
    'challenge.apps.ChallengeConfig',
    'guidebook.apps.GuidebookConfig',
    'lib.apps.LibConfig',
    'sequence.apps.SequenceConfig',
    'tour.apps.TourConfig',
    'leaderboard.apps.LeaderboardConfig',
    'sys_setting.apps.SysSettingConfig',
    'cron_job.apps.CronJobConfig',
    # ========================
    'oauth2_provider',
    'corsheaders',
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django_cleanup.apps.CleanupConfig',
    'bootstrap4',
    'bootstrap_datepicker_plus',
    'mptt',
    'tags_input',
    'rest_framework',
    'colorful',
    'robots'
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning'
}

TAGS_INPUT_MAPPINGS = {
    # 'guidebook.Tag': {'field': 'name'},
    'sys_setting.Tag': {'field': 'name'},
    # 'tour.TourTag': {'field': 'name'}
}

AUTHENTICATION_BACKENDS = (
    'oauth2_provider.backends.OAuth2Backend',
    # Uncomment following if you want to access the admin
    'django.contrib.auth.backends.ModelBackend'
)

MTPU_SCHEME = 'app.mtp.desktop'

OAUTH2_PROVIDER = {
    "AUTHORIZATION_CODE_EXPIRE_SECONDS": 600000000,
    "ACCESS_TOKEN_EXPIRE_SECONDS": 600000000,
    "RESOURCE_SERVER_TOKEN_CACHING_SECONDS": 600000000,
    "ALLOWED_REDIRECT_URI_SCHEMES": [MTPU_SCHEME],
}

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
    'corsheaders.middleware.CorsMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
]

TWO_FACTOR_PATCH_ADMIN = True
TWO_FACTOR_CALL_GATEWAY = None

TWO_FACTOR_SMS_GATEWAY = None
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
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
                # 'django.template.loaders.app_directories.Loader'
            ],
        },
    },
]

# ROBOTS_SITEMAP_VIEW_NAME = 'cached-sitemap'
ROBOTS_USE_HOST = False
ROBOTS_USE_SCHEME_IN_HOST = True
ROBOTS_CACHE_TIMEOUT = 60*60*24

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

AUTH_USER_MODEL = 'accounts.CustomUser'

DEBUG_PROPAGATE_EXCEPTIONS = True

MEDIA_URL = '/media/'
