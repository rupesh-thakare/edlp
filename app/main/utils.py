from app import db
import csv
from app.models import Category, Catalog, ProductInventory


def strip(x):
    if isinstance(x, str):
        return x.strip()
    else:
        return x


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


def add_categories_from_google_sheet(values):
    header = values[0]
    errors = []
    for record in values[1:]:
        if not Category.query.get(strip(record[0])):
            try:
                db_save(Category(
                    category_id=strip(record[0]),
                    category_name=strip(record[1])
                ))
            except Exception as e:
                errors.append({'record': record, 'exception': e})

    return errors


def add_catalog_from_google_sheet(values):
    header = values[0]
    errors = []
    for record in values[1:]:
        if not Catalog.query.get(strip(record[0])):
            try:
                db_save(Catalog(
                    product_id=strip(record[0]),
                    brand=strip(record[1]),
                    description=strip(record[2]),
                    mrp=float(strip(record[3])),
                    category_id=strip(record[4]),
                    size=strip(record[5]),
                    unit=strip(record[6])
                ))
            except Exception as e:
                errors.append({'record': record, 'exception': e})

    return errors


def add_inventory_from_google_sheet(values):
    header = values[0]
    errors = []
    ProductInventory.query.delete()

    try:
        db.session.commit()
    except Exception as e:
        errors.append({'record': None, 'exception': e})
        return errors

    for record in values[1:]:
        try:
            db_save(ProductInventory(
                product_id=strip(record[0]),
                inventory=int(strip(record[1]))
            ))
        except Exception as e:
            errors.append({'record': record, 'exception': e})

    return errors