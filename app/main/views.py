from flask import render_template, url_for, redirect, request
from . import main
from flask_login import login_required, current_user
from .forms import CSRFForm
from .. import db
from ..models import Category, ProductInventory, Orders, Catalog
from datetime import datetime
import pytz
import csv

india_timezone = pytz.timezone('Asia/Kolkata')


def get_aware_current_datetime():
    return india_timezone.localize(datetime.now())


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('main.category'))


@main.route('/categories')
@login_required
def category():
    categories = Category.query.order_by(Category.category_name).all()
    return render_template('categories.html', categories=categories)


@main.route('/products/<category_id>')
@login_required
def product(category_id):
    category = Category.query.filter(Category.category_id == category_id).first()
    products = category.products
    form = CSRFForm()
    return render_template('products.html', category=category, products=products, form=form)


@main.route('/submit-order', methods=['post'])
@login_required
def submit_order():
    form = CSRFForm()
    if form.validate_on_submit():
        # parse form
        products = request.form.getlist('product')
        try:
            db.session.add_all([
                Orders(user_id=current_user.shop_id, date_created=get_aware_current_datetime(), pid=pid) for pid in products
            ])
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            date_now = get_aware_current_datetime()
            date_for_file = f'{date_now.year}-{date_now.month}-{date_now.day}-{date_now.hour}-{date_now.minute}'
            with open(f'missed-orders/missed-orders-{date_for_file}.csv', 'a+', newline='\n', encoding='utf-8') as f:
                fields = ['user_id', 'date_created', 'pid']
                writer = csv.DictWriter(f, fieldnames=fields)
                for pid in products:
                    writer.writerow(dict(user_id=current_user.shop_id, date_created=date_for_file, pid=pid))
        return redirect(url_for('main.category'))
    return redirect(url_for('main.category'))
