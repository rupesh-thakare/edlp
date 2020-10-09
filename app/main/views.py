import os
import pickle

from flask import render_template, url_for, redirect, request, jsonify
from flask_wtf import FlaskForm
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sqlalchemy import and_, func
from . import main
from flask_login import login_required, current_user
from .forms import CSRFForm, SearchForm
from .utils import db_save, find_new_categories, find_new_catalog_entries, add_categories_from_google_sheet, \
    add_catalog_from_google_sheet, add_inventory_from_google_sheet
from .. import db
from ..models import Category, ProductInventory, Orders, Catalog, UploadErrors
from datetime import datetime, timedelta
import pytz
import csv

india_timezone = pytz.timezone('Asia/Kolkata')
DEFAULT_ROUTE = 'main.search'


def get_aware_current_datetime():
    return india_timezone.localize(datetime.now())


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('index.html')
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


@main.route('/downloadorder')
@login_required
def download_orders():
    orderList = Orders.query.filter(func.DATE(Orders.date_created) > ((datetime.utcnow() - timedelta(days=3))))
    return render_template('view_order.html', orders=orderList)


@main.route('/submit-order', methods=['post'])
@login_required
def submit_order():
    form = CSRFForm()
    if form.validate_on_submit():
        # parse form
        products = request.form.getlist('product')
        try:
            db.session.add_all([
                Orders(user_id=current_user.shop_id,
                       date_created=get_aware_current_datetime(),
                       pid=pid,
                       quantity=request.form.get(f'product-qty-{pid}'))
                for pid in products
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

#
# @main.route('/upload', methods=['get', 'post'])
# @login_required
# def upload():
#     form = FlaskForm()
#     if form.validate_on_submit():
#         action = request.form.get('action')
#         file = request.files.get('file')
#         if action == 'category':
#             db_save(find_new_categories(file))
#         elif action == 'catalog':
#             db_save(find_new_catalog_entries(file))
#         else:
#             pass
#         return redirect(url_for('main.upload'))
#     return render_template('upload.html', form=form)


@main.route('/upload')
@login_required
def upload():
    return render_template('upload.html')


@main.route('/google_sheets_upload')
@login_required
def google_sheets_upload():
    creds = None

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    SPREADSHEET_ID = '1NPMXQxzw1D1AfhDpNJvRc8fmREGY35oCTEdFO3kjaQs'
    SHEETS = [{'name': 'category', 'action': add_categories_from_google_sheet},
              {'name': 'catalog', 'action': add_catalog_from_google_sheet},
              {'name': 'inventory', 'action': add_inventory_from_google_sheet}]

    UploadErrors.query.delete()
    db.session.commit()

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            # return render_template('upload.html', message='Credentials invalid. Contact admin')

    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()
    for sheet_data in SHEETS:
        sheet_result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                          range=sheet_data['name']).execute()
        values = sheet_result.get('values', [])

        if not values:
            return render_template('upload.html', message=f'No data found in {sheet}')
        else:
            errors = sheet_data['action'](values)
            sheet_data['errors'] = errors
            db_save([
                UploadErrors(
                    datetime=datetime.now(),
                    model=sheet_data['name'],
                    details=str(error['record']),
                    error=str(error['exception'])
                )
                for error in errors
            ])

    return render_template('upload.html', message=f'Successfully uploaded sheets data', sheet_data=SHEETS)
