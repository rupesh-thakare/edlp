from flask import render_template, url_for, redirect, request, jsonify
from sqlalchemy import and_
from . import main
from flask_login import login_required, current_user
from .forms import CSRFForm, SearchForm
from .. import db
from ..models import Category, ProductInventory, Orders, Catalog
from datetime import datetime
import pytz
import csv

india_timezone = pytz.timezone('Asia/Kolkata')
DEFAULT_ROUTE = 'main.search'


def get_aware_current_datetime():
    return india_timezone.localize(datetime.now())


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for(DEFAULT_ROUTE))


@main.route('/categories')
@login_required
def category():
    form = SearchForm()
    categories = Category.query.order_by(Category.category_name).all()
    return render_template('categories.html', categories=categories, form=form)


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


@main.route('/search/<q>')
@login_required
def search_catalog(q):
    matched_entries_list = []
    if len(q) > 2:
        q_s = q.split()
        search_q = [f'%{s}%' for s in q_s]
        and_filter = [
            Catalog.description.ilike(f'%{s}%')
            for s in q_s
        ]
        # matched_entries = Catalog.query.filter(Catalog.description.ilike(search_q)).all()
        matched_entries = Catalog.query.filter(and_(*and_filter)).all()
        matched_entries_list = [dict(
            mrp=item.mrp,
            brand=item.brand,
            unit=item.unit,
            description=item.description,
            product_id=item.product_id,
            size=item.size,
            inventory=dict(inventory=item.inventory.inventory)
        ) for item in matched_entries]
    return jsonify(matched_entries_list)


@main.route('/search', methods=['get', 'post'])
@login_required
def search():
    form = SearchForm()
    search_result = []
    if form.validate_on_submit():
        q = form.q.data
        search_result = get_matched_data(q)
    return render_template('search.html', search_result=search_result, form=form)


def get_matched_data(search_string):
    if len(search_string) > 2:
        search_terms = search_string.split()
        and_filter_on_search_terms = [
            Catalog.description.ilike(f'%{search_term}%')
            for search_term in search_terms
        ]
        return Catalog.query.filter(and_(*and_filter_on_search_terms)).all()
    else:
        return []


