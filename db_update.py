import csv

def update_category(catalog_file, db, Catalog):
    with open(catalog_file, mode='r') as catalog_file:
        csv_reader = csv.DictReader(catalog_file)
        for record in csv_reader:
            category_id = record['category_id']
            if not Catalog.query.get(category_id):
                try:
                    db.session.add(Catalog(
                        category_id=category_id,
                        category_name=record['category_name'],
                    ))
                    db.session.commit()
                except Exception as e:
                    print(e)


def update_catalog(catalog_file, db, Catalog):
    with open(catalog_file, mode='r') as catalog_file:
        csv_reader = csv.DictReader(catalog_file)
        for record in csv_reader:
            product_id = record['product_id']
            if not Catalog.query.get(product_id):
                try:
                    db.session.add(Catalog(
                        product_id=product_id,
                        brand=record['brand'],
                        description=record['description'],
                        mrp=record['mrp'],
                        category_id=record['category_id'],
                        size=record['size'],
                        unit=record['unit']
                    ))
                    db.session.commit()
                except Exception as e:
                    print(e)
