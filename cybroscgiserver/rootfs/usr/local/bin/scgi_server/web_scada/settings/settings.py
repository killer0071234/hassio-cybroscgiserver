import os
from settings import deploy, settings_local

PROJECT_PATH = os.path.join(
    os.path.realpath(os.path.dirname(__file__)), '..', 'project'
)

DEBUG = not deploy.WEB_DEPLOY
TEMPLATE_DEBUG = DEBUG
DEBUG_TOOLBAR = False

ADMINS = settings_local.ADMINS

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': settings_local.DATABASE_ENGINE,
        'NAME': settings_local.DATABASE_NAME,
        'USER': settings_local.DATABASE_USER,
        'PASSWORD': settings_local.DATABASE_PASSWORD,
        'HOST': settings_local.DATABASE_HOST,
        'PORT': settings_local.DATABASE_PORT
    }
}

EMAIL_HOST = settings_local.SMTP_HOST
EMAIL_HOST_USER = settings_local.SMTP_HOST_USER
EMAIL_HOST_PASSWORD = settings_local.SMTP_HOST_PASSWORD
EMAIL_PORT = settings_local.SMTP_PORT
EMAIL_USE_TLS = settings_local.SMTP_USE_TLS
DEFAULT_FROM_EMAIL = settings_local.DEFAULT_FROM_EMAIL
SERVER_EMAIL = settings_local.SERVER_EMAIL
REPORT_FROM_EMAIL = settings_local.REPORT_FROM_EMAIL
REPORT_EMAIL_SUBJECT = settings_local.REPORT_EMAIL_SUBJECT

try:
    # noinspection PyUnresolvedReferences
    CSV_EXPORT_CHARSET = settings_local.CSV_EXPORT_CHARSET
except NameError:
    CSV_EXPORT_CHARSET = None
except AttributeError:
    CSV_EXPORT_CHARSET = None


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = settings_local.TIME_ZONE
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en"

LANGUAGES = (
    ("en", "English"),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Make this unique, and don't share it with anybody.
SECRET_KEY = settings_local.SECRET_KEY

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_PATH, 'template'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'project.main.context_processors.get_site_name',
                'project.main.context_processors.get_contact_email',
                'project.main.context_processors.get_head_caption',
                'project.main.context_processors.get_footer_text',
                'project.main.context_processors.get_google_webmaster_tools_code',
                'project.main.context_processors.get_shortcut_icon',
            ]
        }
    }
]

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

if DEBUG_TOOLBAR:
    MIDDLEWARE += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

ROOT_URLCONF = 'project.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

if DEBUG_TOOLBAR:
    INSTALLED_APPS += (
        'debug_toolbar',
    )

INSTALLED_APPS += (
    'project.main',
    'project.accounts',
)

CUSTOM_USER_MODEL = 'main.CustomUser'

AUTHENTICATION_BACKENDS = (
    'project.accounts.backends.CustomUserModelBackend',
    'django.contrib.auth.backends.ModelBackend',
)

if DEBUG_TOOLBAR:
    INTERNAL_IPS = ('127.0.0.1',)

    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.timer.TimerPanel',
    )

    DEBUG_TOOLBAR_CONFIG = ({
        'INTERCEPT_REDIRECTS': False,
    })


MEDIA_URL = "/media/"
DATA_URL = "/data/"
CACHE_URL = "/data/"

SCGI_HOST = settings_local.SCGI_HOST
SCGI_PORT = settings_local.SCGI_PORT

PAGE_CACHE_VALIDITY = settings_local.PAGE_CACHE_VALIDITY

DATA_FOLDER_ROOT = os.path.join(settings_local.DATA_DIRECTORY, "media")
MMANAGER_THUMBS_ROOT = os.path.join(settings_local.DATA_DIRECTORY, "thumbs")

CACHE_ROOT = settings_local.DATA_DIRECTORY + "cache/"
CACHE_BACKEND = "file://" + settings_local.DATA_DIRECTORY + "cache/"

DATA_ROOT = settings_local.DATA_DIRECTORY
MEDIA_ROOT = settings_local.DATA_DIRECTORY

SITE_URL = settings_local.SITE_URL

ADMIN_MEDIA_PREFIX = settings_local.ADMIN_MEDIA_PREFIX

STATIC_SETTINGS = settings_local.STATIC_SETTINGS

if not deploy.WEB_DEPLOY:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.SHA1PasswordHasher',
]

STATIC_ROOT = os.path.join(settings_local.SOLAR_PATH, "staticroot")
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(settings_local.SOLAR_PATH, "static"),
]

ALLOWED_HOSTS = settings_local.ALLOWED_HOSTS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'DEBUG'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False
        }
    }
}
