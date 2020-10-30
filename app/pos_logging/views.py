from sqlalchemy.sql import func

from . import pos
from flask import request, jsonify, current_app
import json
from datetime import datetime
from dateutil import parser

from .. import db
from ..main.utils import db_save
from ..models import ShopSalesData, ShopSalesDataLog
import pytz

ist_tz = pytz.timezone('Asia/Kolkata')


@pos.route('/shopdata', methods=['POST'])
def shop_data():
    request_data = request.get_json()
    sales_data = []
    sales_data_log = []

    max_timestamps = dict(
        db.session.query(
            ShopSalesData.shop_id,
            func.max(ShopSalesData.timestamp)
        ).group_by(ShopSalesData.shop_id).all()
    )

    for product_sales in request_data:
        data = sales_data_from_incoming_json(product_sales)
        sales_data_log.append(
            ShopSalesDataLog(
                **data,
                created_timestamp=datetime.now(ist_tz)
            )
        )
        if data['timestamp'] > max_timestamps.setdefault(data['shop_id'], datetime(2000, 1, 1)):
            sales_data.append(
                ShopSalesData(
                    **data
                )
            )

    try:
        db_save(sales_data_log)
        db_save(sales_data)
    except Exception as e:
        try:
            now = datetime.now(ist_tz).strftime('%Y-%m-%d %H-%M-%S')
            with open(f'pos-data/post-data-{now}.json', 'w') as file:
                json.dump(request_data, file)
        except Exception as e:
            return dict(status='error'), 500
    return dict(status='successful'), 201


def sales_data_from_incoming_json(product_sales_data: dict):
    shop_id = product_sales_data.get('shop_id', 'missing_id')
    bill_number = product_sales_data.get('bill_no', 'missing_bill_number')
    barcode = product_sales_data.get('barcode', 'missing_barcode')
    product_description = product_sales_data.get('product_description', 'missing_description')

    try:
        sales_quantity = int(product_sales_data.get('sales_qty', '-1'))
    except:
        sales_quantity = -1

    try:
        amount = float(product_sales_data.get('amount', '-1'))
    except:
        amount = -1

    timestamp = parser.parse(product_sales_data.get('timestamp'))
    date = timestamp.date()

    return dict(
        shop_id=shop_id,
        bill_number=bill_number,
        barcode=barcode,
        product_description=product_description,
        sales_quantity=sales_quantity,
        amount=amount,
        timestamp=timestamp,
        date=date
    )
