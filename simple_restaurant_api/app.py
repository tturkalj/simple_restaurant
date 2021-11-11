from enum import Enum
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from flask import Flask, config, request
from flask_cors import CORS

from database import db
from model import Role, MenuItem, MenuItemType, Table
from api import api, client_api
import config

def get_root_path():
    return os.path.dirname(os.path.abspath(__file__))

def create_app(config_file_name='simple_restaurant_api/config.py'):
    app = Flask('simple_restaurant')
    app.config.from_pyfile(config_file_name)
    app.register_blueprint(api)
    app.register_blueprint(client_api)
    CORS(app, origins=['*'])
    db.init_app(app)
    return app

def init_db(app):
    with app.app_context():
        db.create_all(app=app)
        roles = Role.query.all()
        if not roles:
            roles = (Role(name='waiter'), Role(name='barman'),Role(name='chef'))
            db.session.add_all(roles)
            db.session.commit()

        menu_items = MenuItem.query.all()
        if not menu_items:
            menu_items = (
                MenuItem(item_title='Grilled space-whale steak with algae puree', item_type=MenuItemType.FOOD, item_price=66.50),
                MenuItem(item_title='Tea substitute', item_type=MenuItemType.DRINK, item_price=1.5),
                MenuItem(item_title='Hagro biscuit', item_type=MenuItemType.FOOD, item_price=32.00),
                MenuItem(item_title='Ameglian Major Cow casserole', item_type=MenuItemType.FOOD, item_price=55.75),
                MenuItem(item_title='Pan Galactic Gargle Blaster', item_type=MenuItemType.DRINK, item_price=5.50),
                MenuItem(item_title='Janx Spirit', item_type=MenuItemType.DRINK, item_price=7.70),
                MenuItem(item_title='Tzjin-anthony-ks', item_type=MenuItemType.DRINK, item_price=11.50, item_description='the Gagrakackan version of the gin and tonic.'),
            )
            db.session.add_all(menu_items)
            db.session.commit()

        table = Table.query.all()
        if not table:
            db.session.add(Table())
            db.session.commit()

def init_logger(app):
    log_handler = TimedRotatingFileHandler(
        filename=os.path.join(get_root_path(), config.LOG_FILE_PATH),
        when='midnight',
        backupCount=365
    )
    formatter = logging.Formatter(u'[%(asctime)s] {%(levelname)s - %(message)s')
    log_handler.setFormatter(formatter)
    app.logger.addHandler(log_handler)
    app.logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    app = create_app()
    init_db(app)
    init_logger(app)

    @app.before_request
    def log_request_info():
        app.logger.debug('Route {0} {1}; Request params: {2}'.format(request.path, request.method, (request.values, request.form, request.get_json())))

    app.run(host='localhost', port=config.PORT)
