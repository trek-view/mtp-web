# Map the Paths
This repository is for Map the Paths. 
The user can create a job by selecting the area where photography is required and anyone can apply for this job.
Click [Map the Paths](https://map-the-paths.herokuapp.com/) to experience them.


## Install

- git clone https://github.com/trek-view/map-the-paths.git


### Running on Local

Set DJANGO_SETTINGS_MODULE to config.settings_local in manage.py.
``` python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_local')
```

Fill following values in config/setting_local.py
``` python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

MAPBOX_PUBLISH_TOKEN = 'your_mapbox_token'

MAILERLIST_API_KEY = 'your_maillist_api_key'

MAILERLIST_GROUP_ID = 'your_maillist_aroup_id'

GOOGLE_ANALYTICS = 'your_google_analysis_key'

# EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = os.path.join(BASE_DIR, "sent_emails")

# SMTP settings
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp_host'
DEFAULT_FROM_EMAIL = 'xxx@your_domain'
EMAIL_HOST_USER = 'xxx@your_domain'
EMAIL_HOST_PASSWORD = 'smtp_password'
EMAIL_USE_TLS = True
EMAIL_PORT = 587

SMTP_REPLY_TO = DEFAULT_FROM_EMAIL
```

The following command will build Map the Paths.

``` python
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```


## Deploying with git on Heroku

Create a new app on heroku.
And connect your git repository to the created app.

Set DJANGO_SETTINGS_MODULE to config.settings_heroku in manage.py and config/wsgi.py.
``` python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_heroku')
```

And then push on git.

Run following command. ([Deploying with Git](https://devcenter.heroku.com/articles/git))

### Prerequisites

- PostgreSql 10.0+
- Postgis package
- Python 3.5+
