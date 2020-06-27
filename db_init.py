from app.models import User, Category


def db_init(db):
    db.drop_all()
    db.create_all()


def db_init_data(db):
    db.session.add_all(get_users())
    db.session.add_all(get_categories())
    db.session.commit()


def get_users():
    return [
        User(shop_id='1', password='1'),
        User(shop_id='2', password='2'),
        User(shop_id='3', password='3'),
    ]


def get_categories():
    return [
        Category(category_id=i, category_name=str(i))
        for i in range(5)
    ]


