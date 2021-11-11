# -*- coding: utf-8 -*-
from functools import wraps
import uuid

from flask import Flask, Blueprint, json, request, make_response, jsonify, current_app

from model import MenuItem, Staff, Role, Order, OrderItem, Table, OrderItemStatus
from database import db

def auth_required(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        error_resp = make_response(jsonify({'message':'Unauthorized.'}), 401)
        if auth_header is None:
            return error_resp
        token_parts = auth_header.split('Bearer')
        if len(token_parts) != 2:
            return error_resp
        uuid_part = token_parts[1].strip()
        user = Staff.query.filter_by(bearer_token=uuid_part, deleted=False).first()
        if not user:
            return error_resp
        return fn(*args, **kwargs)
    return decorator


api = Blueprint('api', __name__, url_prefix='/api')
client_api = Blueprint('client_api', __name__, url_prefix='/api')

@api.route('/login', methods=['POST'])
def login():
    request_data = request.get_json()
    role = Role.query.filter_by(name=request_data['role']).first()
    if role is None:
        return make_response(jsonify({'message':'Role %s not found.' % request_data['role']}), 404)
    user = Staff.query.filter_by(username=request_data['username'], role_id=role.id, deleted=False).first()
    bearer_token = str(uuid.uuid4())
    if user is None:
        user = Staff(username=request_data['username'], role_id=role.id, bearer_token=bearer_token)
        db.session.add(user)
    user.bearer_token = bearer_token
    db.session.commit()
    return jsonify({'bearer_token': user.bearer_token})


@api.route('/order-items/<int:order_item_id>', methods=['PUT'])
@auth_required
def order_items_put(order_item_id):
    request_data = request.get_json()
    order_item = OrderItem.query.filter_by(id=order_item_id, item_id=request_data['itemId']).first()
    if not order_item:
        return make_response(jsonify({'message': 'Not found.'}), 404)
    order_item.status = request_data['status']
    db.session.flush()
    all_order_items = OrderItem.query.filter_by(order_id=order_item.order_id).all()
    all_done = all(order_item.status == OrderItemStatus.PREPARING for order_item in all_order_items)
    if all_done:
        for order_item in all_order_items:
            order_item.status = OrderItemStatus.READY_TO_SERVE
    db.session.commit()
    return jsonify({'message': 'OK'})


@api.route('/orders', methods=['GET'])
@auth_required
def orders_get_unfinished():
    has_unfinished_items = request.args.get('has_unfinished_items', False)
    filter_by_status = OrderItem.status.in_((OrderItemStatus.ORDERED, OrderItemStatus.PREPARING, OrderItemStatus.READY_TO_SERVE)) \
                        if has_unfinished_items else OrderItem.status.in_((OrderItemStatus.ORDERED, OrderItemStatus.PREPARING))
    orders = Order.query.join(OrderItem).filter(filter_by_status).all()
    resp = [{
        'order_id': order.id, 
        'table_id': order.table_id,
        'order_items': [{
            'order_item_id': order_item.id,
            'item_id': order_item.item_id,
            'status': order_item.status,
            }for order_item in order.order_items]
        } for order in orders]
    return jsonify(resp)


@client_api.route('/menu-items', methods=['GET'])
def menu_items():
    menu_items = MenuItem.query.all()
    resp = [{
        'item_id': menu_item.id,
        'item_title': menu_item.item_title,
        'item_price': menu_item.item_price,
        'item_type': menu_item.item_type,
        'item_image': menu_item.item_image
    } for menu_item in menu_items]
    return jsonify(resp)


@client_api.route('/orders/<int:order_id>', methods=['GET'])
def orders_get(order_id):
    order = Order.query.filter_by(id=order_id).first()
    if not order:
        return make_response(jsonify({'message': 'Not found.'}), 404)
    
    order_data = {
        'order_id': order.id, 
        'table_id': order.table_id,
        'order_items': []
    }
    order_total = 0
    for order_item in order.order_items:
        order_item_data = {
            'order_item_id': order_item.id,
            'item_id': order_item.item_id,
            'status': order_item.status,
        }
        order_data['order_items'].append(order_item_data)
        order_total += order_item.item.item_price
    order_data['order_total'] = order_total
    return jsonify(order_data)


@client_api.route('/orders', methods=['POST'])
def orders_post():
    request_data = request.get_json()
    table_id = request_data['table_id']
    table = Table.query.filter_by(id=table_id).first()
    if not table:
        return make_response(jsonify({'message': 'Table with id %s not found.' % table_id}), 404)
    items = request_data['items']   
    item_ids = set([item['item_id'] for item in items])
    menu_items = MenuItem.query.filter(MenuItem.id.in_(item_ids)).all()
    menu_item_ids = set([str(menu_item.id) for menu_item in menu_items])
    diff = item_ids.difference(menu_item_ids)
    if diff:
        diff = list(diff)
        return make_response(jsonify({'message': 'Menu items with ids %s not found.' % diff}), 404)
    order = Order(table_id = table_id)
    db.session.add(order)
    db.session.flush()
    order_items = [OrderItem(order_id=order.id, item_id=item['item_id'], status=OrderItemStatus.ORDERED) 
                    for item in items for quantity in range(0, item['quantity'])]
    db.session.add_all(order_items)
    db.session.commit()

    resp = {
        'order_id': order.id,
        'table_id': table.id,
        'order_items': [{
            'order_item_id': order_item.id,
            'item_id': order_item.item_id,
            'status': order_item.status,
        }for order_item in order_items]
    }
    return jsonify(resp)
