import os
import pickle
from datetime import datetime

import pytz

from app import db
from app.main.utils import add_categories_from_google_sheet, add_catalog_from_google_sheet, \
    add_inventory_from_google_sheet, db_save
from app.models import UploadErrors
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def upload_sheet_data():
    try:
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

            # if not values:
            #     return render_template('upload.html', message=f'No data found in {sheet}')
            if not values:
                exit(-1)
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
    except Exception as e:
        UploadErrors(
            datetime=datetime.now(pytz.timezone('Asia/Kolkata')),
            model='unknown',
            details='unknow',
            error=str(e)
        )
