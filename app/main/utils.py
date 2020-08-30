from app import db
import csv
from app.models import Category, Catalog


def db_save(object: 'list or db model'):
    db_add = db.session.add
    if isinstance(object, list):
        db_add = db.session.add_all

    try:
        db_add(object)
        db.session.commit()
    except Exception as e:
        db.session.rollback()


def find_new_categories(file):
    new_categories = []
    for record in csv.DictReader((r.decode('utf-8') for r in file.readlines())):
        if not Category.query.get(record['category_id']):
            new_categories.append(
                Category(
                    category_id=record['category_id'],
                    category_name=record['category_name']
                )
            )
    return new_categories


def find_new_catalog_entries(file):
    new_entries = []
    for record in csv.DictReader((r.decode('utf-8') for r in file.readlines())):
        if not Catalog.query.get(record['product_id']):
            new_entries.append(Catalog(
                product_id=record['product_id'],
                brand=record['brand'],
                description=record['description'],
                mrp=record['mrp'],
                category_id=record['category_id'],
                size=record['size'],
                unit=record['unit']
            ))
    return new_entries
