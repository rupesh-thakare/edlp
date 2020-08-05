from flask import Blueprint

pos = Blueprint('post', __name__)

from . import views
