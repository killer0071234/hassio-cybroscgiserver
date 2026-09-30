# -*- coding: utf-8 -*-
import os

from settings import version

SOLAR_PATH = os.path.normpath(
    os.path.join(os.path.realpath(os.path.dirname(__file__)), '..')
)
ADMINS = (
    ('Cybrotech', 'info@cybrotech.hr'),
)

SCGI_HOST = 'localhost' # scgi server location
SCGI_PORT = 4000        # scgi server port number

DATABASE_ENGINE =   'django.db.backends.mysql'  # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME =     'solar3'                     # Or path to database file if using sqlite3.
DATABASE_USER =     'solar'                     # Not used with sqlite3.
DATABASE_PASSWORD = 'solar'                     # Not used with sqlite3.
DATABASE_HOST =     ''                          # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT =     ''                          # Set to empty string for default. Not used with sqlite3.

REPORT_FROM_EMAIL =     'noreply@...' # from address in e-mails sent by reporting engine
REPORT_EMAIL_SUBJECT =  'CybroWebScada report' # subject in e-mails sent by reporting engine
DEFAULT_FROM_EMAIL =    'noreply@...' # from address for error emails
SERVER_EMAIL =          'noreply@...' # from address for django.core.mail.mail_admins() and django.core.mail.mail_managers()

SMTP_HOST = 'smtp.dummy.com'
SMTP_HOST_USER = 'solar_noreply'
SMTP_HOST_PASSWORD = ''
SMTP_PORT = 25
SMTP_USE_TLS = False

TIME_ZONE = 'Europe/Zagreb'
SECRET_KEY = '$$|Y6_0f]6$1&^8Wv4673;J%JR-b%ln@iV6?AhI.5,t?>`kS'

SITE_URL = 'http://solarserver'
PAGE_CACHE_VALIDITY = 3600 # seconds
ADMIN_MEDIA_PREFIX = '/media/admin/'
DATA_DIRECTORY = os.path.join(SOLAR_PATH, 'data')
CYBRO_SCGI_SERVER_DIRECTORY = os.path.normpath(os.path.join(SOLAR_PATH, '..'))
TIMEPLOT_INTERPOLATION = 4 # cumulative timeplot, defines how many bars left and right to take into account

STATIC_SETTINGS = {
    "site_name": "CybroWebScada",
    "contact_email": "mailto:info@cybrotech.com?subject=CybroWebScada",
    "head_caption": "CybroWebScada",
    "footer_text": "CybroWebScada v%s, copyright &copy; 2010-2024" % version.WebSoftwareVersion,
    "google_webmaster_tools_code": "",
    "shortcut_icon": "/static/misc/favicon.ico",
}

ALLOWED_HOSTS = ['*', 'www.example.com', 'localhost', '127.0.0.1'] # list of domains or IP addresses allowed to serve the application
