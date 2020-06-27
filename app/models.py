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
    mrp = db.Column(db.Integer)
    category_id = db.Column(db.String(64), db.ForeignKey('categories.category_id'))
    size = db.Column(db.String(128))
    unit = db.Column(db.String(64))
    inventory = db.relationship('ProductInventory', backref='product', lazy='joined')


class ProductInventory(db.Model):
    __tablename__ = 'product_inventory'
    proudct_id = db.Column(db.String(128), db.ForeignKey('catalog.product_id'), primary_key=True)
    inventory = db.Column(db.Integer)


class Orders(db.Model):
    __tablename__ = 'orders_received'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), db.ForeignKey('users.shop_id'))
    date_created = db.Column(db.DateTime)
    pid = db.Column(db.String(64), db.ForeignKey('catalog.product_id'))


@login_manager.user_loader
def load_user(shop_id):
    return User.query.get(int(shop_id))
