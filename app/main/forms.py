from flask_wtf import FlaskForm
from wtforms import StringField


class CSRFForm(FlaskForm):
    pass


class SearchForm(FlaskForm):
    q = StringField()
