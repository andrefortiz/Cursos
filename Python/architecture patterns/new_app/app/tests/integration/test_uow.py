import threading
import time
import traceback

import pytest

from domains import model
from new_app.app.tests.random_def import random_sku, random_batchref
from services import unit_of_work


def try_to_allocate(orderid, sku, exceptions):
    line = model.OrderLine(orderid, sku, 10)
    try:
        with unit_of_work.ProductSqlAlchemyUnitOfWork() as uow:
            product = uow.products.get(sku=sku)
            product.allocate(line)
            time.sleep(0.2)
            uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)


def test_concurrent_updates_to_version_are_not_allowed(session_factory_real_db):
    sku = random_sku('1')
    batch = random_batchref('1')
    session = session_factory_real_db()

    batch = insert_batch(session, batch, sku, 100, eta=None)
    insert_product(session, sku,  [batch], version_number=1)
    session.commit()


    # sku = 'HIPSTER-WORKBENCH'
    # batch = 'b1'


    order1, order2 = 'o1', 'o2'
    exceptions = []  # type: List[Exception]

    try_to_allocate_order1 = lambda: try_to_allocate(order1, sku, exceptions)
    try_to_allocate_order2 = lambda: try_to_allocate(order2, sku, exceptions)

    thread1 = threading.Thread(target=try_to_allocate_order1)
    thread2 = threading.Thread(target=try_to_allocate_order2)

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    [[version]] = session.execute(
        'SELECT version_number FROM products WHERE sku=:sku',
        dict(sku=sku)
    )

    assert version == 2
    #if len(exceptions) > 0:
    #    [exception] = exceptions
    #    assert 'could npt serialize access due to concurrent update' in str(exception)

    orders = list(session.execute(
        'SELECT orderid FROM allocations '
        '  JOIN batches ON allocations.batch_id=batches.id'
        '  JOIN order_lines ON allocations.orderline_id=order_lines.id'
        ' WHERE order_lines.sku=:sku',
        dict(sku=sku)
    ))
    assert len(orders) == 1
    with unit_of_work.SqlAlchemyUnitOfWork as uow:
        uow.session.execute('select 1')


def test_uow_can_save_product_and_batch_and_allocate_it(session_factory):

    uow = unit_of_work.ProductSqlAlchemyUnitOfWork(session_factory)
    session = session_factory()
    sku = 'HIPSTER-WORKBENCH3'
    with uow:
        product = model.Product(sku, [model.Batch('b3', sku, 100, None)])
        uow.products.add(product)
        # product.batches.append()
        prodcut2 = uow.products.get_by_batchref('b3')
        product = uow.products.get(sku=sku)
        line = model.OrderLine('o3', sku, 10)
        product.allocate(line)
        uow.commit()
        batchref = get_allocated_batch_ref(session, 'o3', sku)
        assert batchref == 'b3'


def test_uow_can_retrieve_a_batch_and_allocate_to_it(session_factory):
    sku = 'HIPSTER-WORKBENCH'

    session = session_factory()
    batch = insert_batch(session, 'batch1', sku, 100, None)
    insert_product(session, sku, [batch], version_number=1)
    session.commit()
    uow = unit_of_work.ProductSqlAlchemyUnitOfWork(session_factory)

    with uow:
        product = uow.products.get(sku=sku)
        line = model.OrderLine('o1', sku, 10)
        product.allocate(line)
        uow.commit()
        batchref = get_allocated_batch_ref(session, 'o1', sku)
        assert batchref == 'batch1'


def test_rolls_back_uncommitted_work_by_default(session_factory):
    uow = unit_of_work.ProductSqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session, 'batch1', 'MEDIUM-PLINTH', 100, None)
    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM batches'))
    assert rows == []


def test_list_baches(session_factory):
    uow = unit_of_work.ProductSqlAlchemyUnitOfWork(session_factory)
    with uow:
        batches = uow.products.list_batches()

    assert batches == []

def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.ProductSqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, 'batch1', 'LARGE-FORK', 100, None)
            raise MyException()

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []


def insert_product(session, sku, batches, version_number):
    session.execute('INSERT INTO products (sku, version_number)'
                    ' VALUES (:sku, :version_number)',
                    dict(sku=sku, version_number=version_number))

    return model.Product(sku, batches, version_number)


def insert_batch(session, ref, sku, qty, eta):
    session.execute('INSERT INTO batches (reference, sku, _purchased_quantity, eta)'
                    ' VALUES (:ref, :sku, :qty, :eta)',
                    dict(ref=ref, sku=sku, qty=qty, eta=eta))

    return model.Batch(ref, sku, qty, eta)


def get_allocated_batch_ref(session, orderid, sku):
    [[orderlineid]] = session.execute(
        'SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku',
        dict(orderid=orderid, sku=sku)
    )
    [[batchref]] = session.execute(
        'SELECT b.reference FROM allocations JOIN batches AS b on batch_id = b.id'
        ' WHERE orderline_id=:orderlineid',
        dict(orderlineid=orderlineid)
    )
    return batchref