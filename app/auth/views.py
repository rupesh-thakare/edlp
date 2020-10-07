from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, \
    current_user
from . import auth
from .. import db
from ..models import User
from .forms import LoginForm


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(shop_id=form.shop_id.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, remember=True)
            next = request.form.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.search')
            return redirect(next)
        else:
            return redirect(url_for('auth.login', next=request.form.get('next', '')))
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))
