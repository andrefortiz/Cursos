from datetime import datetime

from flask import Flask, jsonify, request
import json

from sqlalchemy.orm import sessionmaker

import bootstrap
import views
from adapters import orm
from config import get_sqlite_engine
from domains import commands
from domains.model import OutOfStock
from services import unit_of_work
from services.handlers import InvalidSku
from services.messagebus import MessageBus

app = Flask(__name__)
#orm.start_mappers()
bus = bootstrap.bootstrap()
#get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
#get_session = sessionmaker(bind=get_sqlite_engine())
#app.debug = True

print('chegou ate aqui Flask App - Debian 10')

@app.route("/")
def hello():
    return "Hello World Flask App - Debian 10"


@app.route('/add_batch', methods=['POST'])
def batches():
    #orm.start_mappers()
    try:
        eta = request.json['eta']
        if eta is not None:
            eta = datetime.fromisoformat(eta).date()
        command = commands.CreateBatch(
            request.json['ref'],
            request.json['sku'],
            request.json['qty'],
            eta
        )
        # uow = unit_of_work.ProductSqlAlchemyUnitOfWork(get_session)
        # bus.handle(command, uow)
        bus.handle(command)
        return 'OK', 201
    except Exception as e:
        return jsonify({'message': str(e)}), 400


@app.route('/allocate', methods=['POST'])
def allocate_endpoint():
    try:
        #command = commands.Allocate.from_json(request.json)

        command = commands.Allocate(
            request.json['orderid'],
            request.json['sku'],
            request.json['qty'],
        )
        results = MessageBus().handle(command, unit_of_work.ProductSqlAlchemyUnitOfWork(get_session))
        batchref = results.pop(0)
    except (OutOfStock, InvalidSku, Exception) as e:
        return jsonify({'message': str(e)}), 400

    return jsonify({'batchref': batchref}), 202


@app.route('/allocations/<orderid>', methods=['GET'])
def allocations_view_endpoint(orderid):
    uow = unit_of_work.ProductSqlAlchemyUnitOfWork(get_session)
    result = views.allocations(orderid, uow)
    if not result:
        return jsonify({'message': 'order not found'}), 404
    return jsonify(result), 200


#testes
@app.route('/product', methods=['POST'])
def get_by_ref():
    try:
        uow = unit_of_work.ProductSqlAlchemyUnitOfWork(get_session)
        command = commands.GetProductByRef(request.json['ref'])
        product = MessageBus().handle(command, uow)

        return_object = {}
        if product[0] is not None:
            return_object = {"sku": product[0].sku,
                        "version_number": product[0].version_number}
        return json.dumps({"product": return_object}, indent=3), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400


@app.route('/batches', methods=['POST'])
def list_batches():
    try:
        uow = unit_of_work.ProductSqlAlchemyUnitOfWork(get_session)
        command = commands.GetBaches(request.json['ref'])
        product = MessageBus().handle(command, uow)

        batches = []
        if product[0] is not None:
            batches = [{"reference": v.reference, "sku": v.sku,
                        "purchased_quantity": v._purchased_quantity}
                            for v in product[0]]
        return json.dumps({"batches": batches}, indent=3), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400


@app.route('/products', methods=['POST'])
def list_products():
    try:
        uow = unit_of_work.ProductSqlAlchemyUnitOfWork(get_session)
        command = commands.GetProducts(request.json['sku'])
        products = MessageBus().handle(command, uow)

        return_products = []
        if products is not None and len(products) > 0:
            return_products = [{"sku": p.sku, "version_number": p.version_number}
                        for p in products[0]]
        return json.dumps({"products": return_products}, indent=3), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@app.route('/order_lines', methods=['GET'])
def list_order_lines():
    try:
        uow = unit_of_work.ProductSqlAlchemyUnitOfWork(get_session)
        command = commands.GetOrderLines(" ")
        order_lines = MessageBus().handle(command, uow)

        return_list = []
        if order_lines is not None and len(order_lines) > 0:
            return_list = [{"orderid": o.orderid, "sku": o.sku, "qty": o.qty}
                        for o in order_lines[0]]
        return json.dumps({"order_lines": return_list}, indent=3), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400


"""
@app.route('/allocate', methods=['POST'])
def allocate_endpoint():
    session = get_session()

    repo = repository.SqlAlchemyRepository(session)

    line = OrderLine(
        request.json['orderid'],
        request.json['sku'],
        request.json['qty'],
    )

    try:
        batchref = handlers.allocate(line.orderid, line.sku, line.qty, repo, session)
    except (OutOfStock, InvalidSku) as e:
        return jsonify({'message': str(e)}), 400

    return jsonify({'batchref': batchref}), 201
"""

