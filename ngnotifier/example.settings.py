"""
Django settings for ng-notifier project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

"""
import os

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP
from django.utils.translation import ugettext_lazy as _



# SITE PARAMETERS

SITE_NAME = "NG Notifier"
DOMAIN = 'http://localhost/' # Must end with a slash! /!\
SITE_URL_PREFIX = '' # Empty or your-prefix/ <- Must end with a slash /!\
SITE_URL = DOMAIN + SITE_URL_PREFIX

SECRET_KEY = ''

DEBUG = False
TEMPLATE_DEBUG = False

LOGIN_REDIRECT_URL = '/settings'

# DIRECTORIES
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
APP_DIR = os.path.dirname(BASE_DIR)
LOCALE_PATHS = (os.path.join(BASE_DIR, "web", "locale"),)
TEMPLATE_DIRS = (BASE_DIR + '/templates',)
STATIC_ROOT = APP_DIR + '/static/'
STATICFILES_DIRS = (APP_DIR + '/web/static/',)

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

AUTH_USER_MODEL = 'ngnotifier.User'
PASSWORD_HASHERS = ('django.contrib.auth.hashers.PBKDF2PasswordHasher',)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ngnotifier',
    'captcha',
    'apscheduler',
    'rest_framework',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

ROOT_URLCONF = 'ngnotifier.urls'
WSGI_APPLICATION = 'ngnotifier.wsgi.application'

X_FRAME_OPTIONS = 'DENY'

# DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    # 'defaults': {
    #     'ENGINE': 'django.db.backends.postgresql_psycopg2',
    #     'NAME': '',
    #     'USER': '',
    #     'PASSWORD': '',
    #     'HOST': 'localhost',
    #     'PORT': 5432
    # }
}
DATABASE_USE = 'sqlite'


# I18N
LANGUAGE_CODE = 'en-en'
TIME_ZONE = 'Europe/Paris'
LANGUAGES = (
    ('en', _('English')),
)

USE_I18N = False
USE_L10N = True
USE_TZ = True


# STATICS
STATIC_URL = '/' + SITE_URL_PREFIX + 'static/'

# CONTEXT PROCESSORS -> adds some 'global' variables for templates
TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
    'ngnotifier.context_processors.site_infos'
)


# **** NOTIFS CONFIG **** #

# Tag to be added to the message object
BOT_TAG = '[BOT]'  # Example: News title here [BOT]

# Message to be displayed at the end of the news.
BOT_MSG = '\nThis message has been sent automatically by the *NG NOTIFIER BOT*.'

SEND_FROM_POSTER = False  # Send the mail from the address of the news poster
FROM_ADDR = 'ng-notifier@42portal.com'

mail_conf = {
    'address': '',
    'host': '',
    'port': 0,
    'user': '',
    'pass': '',
    'ssl': True
}


# **** CELERY CONFIG **** #

SECONDS_DELTA = 60  # Time delta between two checks

# **** HOSTS CONFIG **** #

hosts = {
    'news.epita.fr':
        {
            'host': 'news.epita.fr',
            'port': 119,
            'user': None,
            'pass': None,
            'ssl': False,
            'encoding': 'utf-8',
            'timeout': 30,
            'groups': [],  # Empty means get all groups
        },
}

users = {}  # {
# 'Me':
#        {
#            'mail': 'me@me.me',
#            'password': '',
#            'admin': False,
#            'notifs': {
#                'pushbullet': True,
#                'mail': True
#            },
#            'pushbullet_api_key': 'somethingherethatisabase64md5',
#            'subscriptions': [
#            ]
#        },
#    }
