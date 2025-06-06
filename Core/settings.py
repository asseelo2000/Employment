"""
Django settings for Core project.

Generated by 'django-admin startproject' using Django 5.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    'django.contrib.humanize',
    "Employment",
    "location_field.apps.DefaultConfig",
    "smart_selects",
    "django_select2",
    "advanced_filters",
    "helpdesk",
    'bootstrap4form',
    "help_desk_account",
    "pinax.invitations",
    "pinax.teams",
    "reversion",
    'rest_framework',
    "django_mail_admin",
    "post_office",

    "channels",
    "chat",

       ]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "Core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR /"templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "helpdesk.context_processors.default_queue",
            ],
        },
    },
]

WSGI_APPLICATION = "Core.wsgi.application"

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],  # Redis server
        },
    },
}


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    "Core/static",
]


# media files configuratino start

# The URL that will serve media files
MEDIA_URL = "/media/"

# The directory where uploaded media files will be stored on the server
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Session expires after 30 minutes of inactivity
SESSION_COOKIE_AGE = 1800  # 30 minutes in seconds
SESSION_SAVE_EVERY_REQUEST = True  # Reset the session timer on each request

# Celery Configuration
CELERY_BROKER_URL = (
    "redis://localhost:6379"  # Adjust if Redis is on a different host or port
)
CELERY_RESULT_BACKEND = "redis://localhost:6379"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Riyadh"

# Google maps configuratino
GOOGLE_API_KEY = ""
LOCATION_FIELD = {
    "search.provider": "google",
    "provider.google.api": "//maps.google.com/maps/api/js?sensor=false",
    "provider.google.api_key": GOOGLE_API_KEY,
    "provider.google.api_libraries": "places",
    "provider.google.map.type": "ROADMAP",
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "select2": {
        # "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "treenode": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

SELECT2_CACHE_BACKEND = "select2"

# Helpdesk settings 
HELPDESK_DEFAULT_QUEUE = 'employment-internal'
HELPDESK_STAFF_ONLY_TICKET_OWNERS = True  # Only supervisors can own tickets
HELPDESK_SUBMITTERS_CAN_ACCESS_TICKETS = False  # Regular users can’t see tickets
DEFAULT_FILE_STORAGE = 'media/issues'
SITE_ID = 1


# Token Support sends to Employment2 for submitting tickets

SUPPORT_API_KEY = config('SUPPORT_API_KEY') # Token Employment2 sends to Support for submitting tickets
# Token Employment2 expects from Support for receiving feedback
EMPLOYMENT2_API_KEY = config('EMPLOYMENT2_API_KEY')  # Matches SUPPORT_API_KEY
SUPPORT_SUBMIT_URL = config('SUPPORT_SUBMIT_URL')
# SUPPORT_FEEDBACK_URL = 'http://127.0.0.1:8000/employment/feedback/'




ACCOUNT_TIMEZONES = []
ACCOUNT_LANGUAGES = []
ACCOUNT_EMAIL_UNIQUE= []
ACCOUNT_PASSWORD_STRIP = ""
ACCOUNT_CREATE_ON_SAVE = True

# Language and timezone settings
LANGUAGE_CODE = 'ar'  # Set Arabic as the default language
TIME_ZONE = 'Asia/Aden'  # Set the timezone to Riyadh

USE_I18N = True
USE_L10N = True
USE_TZ = True
