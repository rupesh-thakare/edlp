from datetime import timedelta

from utils import get_random_string
import os

DEBUG = True
SECRET_KEY = get_random_string()

basedir = os.path.abspath(os.path.dirname(__package__))
db_path = os.path.join(basedir, 'data-dev.sqlite')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_recycle': 289 #PythonAnywhere sets timeout of sessions to 5 minutes. So to avoid disconnects setting this to less than 300 seconds
}

REMEMBER_COOKIE_DURATION = timedelta(days=90)
