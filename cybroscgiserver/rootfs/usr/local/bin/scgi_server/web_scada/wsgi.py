#!/usr/bin/env python3
import os
import sys

import pymysql
from django.core.wsgi import get_wsgi_application

APPLICATION_NAME = "solar"
HOME_DIR = os.path.normpath(os.path.join(
    os.path.realpath(os.path.dirname(__file__)), '..', '..'
))

sys.path = [
    os.path.join(HOME_DIR, 'app', 'web_scada'),
    os.path.join(HOME_DIR, 'app', 'web_scada', 'project'),
] + sys.path


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
pymysql.install_as_MySQLdb()

application = get_wsgi_application()
