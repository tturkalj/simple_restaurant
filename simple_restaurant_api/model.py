from enum import Enum

from database import db

class Items(db.Model):
    item = db.Column(db.Unicode(length=1024))

class Role(db.Model):
    name = db.Column(db.Unicode(length=1024))

class Staff(db.Model):
    username = db.Column(db.Unicode(length=1024), nullable=False)
    bearer_token = db.Column(db.Unicode(length=1024), nullable=False)
    role_id = db.Column(db.ForeignKey('role.id'), nullable=False, index=True)

    role = db.relationship('Role')

class MenuItemType(str, Enum):
    FOOD = 'food'
    DRINK = 'drink'

class MenuItem(db.Model):
    item_title = db.Column(db.Unicode(length=1024), nullable=False)
    item_price = db.Column(db.Integer, nullable=False)
    item_description = db.Column(db.UnicodeText)
    item_type = db.Column(db.Unicode(length=1024), nullable=False)
    item_image = db.Column(db.UnicodeText)

class Table(db.Model):
    pass

class Order(db.Model):
    table_id = db.Column(db.ForeignKey('table.id'), nullable=False, index=True)

    table = db.relationship('Table', backref=db.backref('orders', lazy='dynamic'))

class OrderItemStatus(str, Enum):
    ORDERED = 'ordered'
    PREPARING = 'preparing'
    READY_TO_SERVE = 'ready_to_serve'
    DELIVERED = 'delivered'

class OrderItem(db.Model):
    order_id = db.Column(db.ForeignKey('order.id'), nullable=False, index=True)
    item_id = db.Column(db.ForeignKey('menu_item.id'), nullable=False, index=True)
    status = db.Column(db.Unicode(length=1024), nullable=False)

    order = db.relationship('Order', backref=db.backref('order_items', lazy='dynamic'))
    item = db.relationship('MenuItem',)
