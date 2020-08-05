from . import pos
from flask import request, jsonify, current_app
import json
from datetime import datetime


@pos.route('/shopdata', methods=['POST'])
def shop_data():
    request_data = request.get_json()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        with open(f'pos-data/post-data-{now}.json', 'w') as file:
           json.dump(request_data, file)
    except Exception as e:
        return dict(status='error'), 500
    return dict(status='successful'), 201
