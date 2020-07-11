from datetime import timedelta

from utils import get_random_string
import os

DEBUG = True
SECRET_KEY = get_random_string()

basedir = os.path.abspath(os.path.dirname(__package__))
db_path = os.path.join(basedir, 'data-dev.sqlite')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

REMEMBER_COOKIE_DURATION = timedelta(days=90)