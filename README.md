# Map the Paths
This repository is for Map the Paths. 
The user can create a job by selecting the area where photography is required and anyone can apply for this job.
Click [Map the Paths](https://map-the-paths.herokuapp.com/) to experience them.


## Install

- git clone https://github.com/trek-view/mtp-web.git


### Running on Local

Set DJANGO_SETTINGS_MODULE to config.settings.local in manage.py.
``` python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
```

Fill following values in config/setting/local.py
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

```

The following command will build Map the Paths.

``` python
pip install -r requirements.txt
python manage.py migrate
```

Run following command to create super admin.
```
python manage.py createsuperuser
```
Run following command to run server.
```
python manage.py runserver
```


## Deploying with git on Heroku

Create a new app on heroku.
And connect your git repository to the created app.

Set DJANGO_SETTINGS_MODULE to config.settings_heroku in manage.py and config/wsgi.py.
``` python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.heroku')
```

And then push on git.

Run following command. ([Deploying with Git](https://devcenter.heroku.com/articles/git))

Quick install and run server using cli on heroku:
```
heroku git:remote -a your_heroku_app
git push heroku [git_branch:]master
heroku run python manage.py migrate [-a your_heroku_app]
heroku run python manage.py collectstatic --noinput [-a your_heroku_app]
heroku run python manage.py createsuperuser [-a your_heroku_app]
```

Run following command to check logs.
```
heroku logs --tail [-a your_heroku_app]
```

### Prerequisites

- PostgreSql 10.0+
- Postgis package
- Python 3.6+
