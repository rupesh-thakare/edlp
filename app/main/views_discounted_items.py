from flask import render_template
from flask_login import login_required

from .forms import CSRFForm
from .views import main, set_discounted_price
from .. import db
from ..models import Catalog


@main.route('/discounted-items')
@login_required
def discounted_items_home():
    # discounted_products = Catalog.query.filter(Catalog.discount > 0).order_by(Catalog.brand.asc()).all()
    # discounted_products = list(map(set_discounted_price, discounted_products))
    discounted_products = None
    discounted_brands =  db.session.query(Catalog.brand.distinct())\
        .filter(Catalog.discount > 0)\
        .order_by(Catalog.brand.asc())\
        .all()
    return render_template('discounted-items-home.html',
                           discounted_products=discounted_products,
                           discounted_brands=discounted_brands)


@main.route('/discounted-items/brand-products/<brand_name>')
@login_required
def discounted_items_brand_products(brand_name):
    discounted_products = Catalog.query\
        .filter(Catalog.discount > 0, Catalog.brand == brand_name)\
        .order_by(Catalog.description.asc())\
        .all()
    discounted_products = list(map(set_discounted_price, discounted_products))
    form = CSRFForm()
    return render_template('discounted-items-brand-products.html',
                           discounted_products=discounted_products,
                           brand_name=brand_name,
                           form=form)