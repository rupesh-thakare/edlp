from flask_login import UserMixin
from . import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    shop_id = db.Column(db.String(64), primary_key=True)
    password = db.Column(db.String(128))

    def verify_password(self, password):
        return self.password == password

    def get_id(self):
        return self.shop_id

    def __repr__(self):
        return '<User %r>' % self.shop_id


class Category(db.Model):
    __tablename__ = 'categories'
    category_id = db.Column(db.String(64), primary_key=True)
    category_name = db.Column(db.String(256))
    products = db.relationship('Catalog', backref='category')


class Catalog(db.Model):
    __tablename__ = 'catalog'
    product_id = db.Column(db.String(128), primary_key=True)
    brand = db.Column(db.String(128))
    description = db.Column(db.String(1024))
    mrp = db.Column(db.Float)
    category_id = db.Column(db.String(64), db.ForeignKey('categories.category_id'))
    size = db.Column(db.String(128))
    unit = db.Column(db.String(64))
    discount = db.Column(db.Float, default=0)


class ProductInventory(db.Model):
    __tablename__ = 'product_inventory'
    product_id = db.Column(db.String(128), primary_key=True)
    inventory = db.Column(db.Integer)


class Orders(db.Model):
    __tablename__ = 'orders_received'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), db.ForeignKey('users.shop_id'))
    date_created = db.Column(db.DateTime)
    pid = db.Column(db.String(64))
    quantity = db.Column(db.Integer, default=0)


class UploadErrors(db.Model):
    __tablename__ = 'upload_errors'

    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DATETIME)

    model = db.Column(db.String(64))
    details = db.Column(db.TEXT)
    error = db.Column(db.TEXT)


class ShopSalesData(db.Model):
    __tablename_ = 'shop_sales_data'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DATE)
    timestamp = db.Column(db.DATETIME)
    shop_id = db.Column(db.String(64))
    bill_number = db.Column(db.String(64))
    barcode = db.Column(db.String(64))
    product_description = db.Column(db.String(1024))
    sales_quantity = db.Column(db.Integer)
    amount = db.Column(db.Float)


class ShopSalesDataLog(db.Model):
    __tablename_ = 'shop_sales_data_log'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DATE)
    timestamp = db.Column(db.DATETIME)
    shop_id = db.Column(db.String(64))
    bill_number = db.Column(db.String(64))
    barcode = db.Column(db.String(64))
    product_description = db.Column(db.String(1024))
    sales_quantity = db.Column(db.Integer)
    amount = db.Column(db.Float)
    created_timestamp = db.Column(db.DATETIME)


@login_manager.user_loader
def load_user(shop_id):
    try:
        return User.query.get(shop_id)
    except Exception as e:
        db.session.rollback()
        return None
