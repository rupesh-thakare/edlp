import os
import pickle
from pprint import pprint

from flask import render_template, url_for, redirect, request, jsonify
from flask_wtf import FlaskForm
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sqlalchemy import and_, func
from werkzeug.exceptions import InternalServerError

from . import main
from flask_login import login_required, current_user
from .forms import CSRFForm, SearchForm
from .utils import db_save, find_new_categories, find_new_catalog_entries, add_categories_from_google_sheet, \
    add_catalog_from_google_sheet, add_inventory_from_google_sheet, get_google_sheets_credentials
from .. import db
from ..models import Category, ProductInventory, Orders, Catalog, UploadErrors, ShopSalesData
from datetime import datetime, timedelta
import pytz
import csv

india_timezone = pytz.timezone('Asia/Kolkata')
DEFAULT_ROUTE = 'main.search'


def get_aware_current_datetime():
    return datetime.now(india_timezone)


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
    products = [p for p in products if p.inventory and p.inventory.inventory > 0]
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
        search_result = [s for s in search_result if s.inventory and s.inventory.inventory > 0]
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
                    datetime=datetime.now(pytz.timezone('Asia/Kolkata')),
                    model=sheet_data['name'],
                    details=str(error['record']),
                    error=str(error['exception'])
                )
                for error in errors
            ])

    return render_template('upload.html', message=f'Successfully uploaded sheets data', sheet_data=SHEETS)


@main.route('/shop_data_export')
def shop_data_export():
    google_sheets_credentials = get_google_sheets_credentials()
    if not google_sheets_credentials:
        raise InternalServerError('Google sheets credentials invalid')

    SPREADSHEET_ID = '1EVAHeUcqszrtAftpv8jN3lJtrBHnCM-F2MNej1Izy7o'
    service = build('sheets', 'v4', credentials=google_sheets_credentials)

    workbook = service.spreadsheets()
    workbook_data = workbook.get(spreadsheetId=SPREADSHEET_ID).execute()

    new_shop_ids = db.session.query(ShopSalesData.shop_id.distinct()).filter(
        ShopSalesData.date > (datetime.today().date() - timedelta(days=10))
    ).all()
    new_shop_ids = [i[0] for i in new_shop_ids]

    previous_sheet_delete_requests = [
        {
            "deleteSheet": {
                "sheetId": sheet['properties']['sheetId']
            }
         }
        for sheet in workbook_data['sheets']
        if sheet['properties']['title'] != 'the-one-you-cant-delete'
    ]
    add_new_sheet_requests = [
        {
            "addSheet": {
                "properties": {
                    "title": sheet_name,
                }
            }
        }
        for sheet_name in new_shop_ids
    ]

    requests = previous_sheet_delete_requests + add_new_sheet_requests

    batch_update_spreadsheet_request_body = {
        'requests': requests
    }

    response = workbook.batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=batch_update_spreadsheet_request_body
    ).execute()

    shop_sales_data = ShopSalesData.query.filter(
        ShopSalesData.shop_id.in_(new_shop_ids),
        ShopSalesData.date > (datetime.today().date() - timedelta(days=10))
    ).all()

    sales_divided_by_shop = {}

    for sales_data in shop_sales_data:
        shop_data = sales_divided_by_shop.setdefault(
            sales_data.shop_id,
            [['shop_id', 'date', 'bill_number', 'barcode', 'product_description', 'quantity', 'amount']]
        )
        shop_data.append([sales_data.shop_id, str(sales_data.date), sales_data.bill_number, sales_data.barcode,
                           sales_data.product_description, sales_data.sales_quantity, sales_data.amount])

    sales_data_for_sheet_body = [
        {
            'range': key,
            'values': sales_divided_by_shop[key]
        }
        for key in sales_divided_by_shop
    ]

    sheet_request_body = {
        'valueInputOption': 'USER_ENTERED',
        'data': sales_data_for_sheet_body
    }

    workbook.values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=sheet_request_body
    ).execute()

    return {'result': 'success'}