from adapters import repository
from domains.model import Batch, OrderLine, Product


def test_repository_can_retrieve_a_batch_wit_allocations(session):
    orderline_id = insert_order_line(session)
    batch1_id = insert_batch(session, 'batch1')
    insert_batch(session, 'batch2')
    insert_allocation(session, orderline_id, batch1_id)

    repo = repository.SqlAlchemyRepository(session)
    retrieved = repo.get('batch1')

    expected = Batch('batch1', 'GENERIC-SOFA', 100, eta=None)
    assert retrieved == expected #batch.__eq__ only compares reference
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {
        OrderLine('order1', 'GENERIC-SOFA', 12),
    }


def test_respository_can_save_batch(session):
    sku = 'RUSTY-SOAPDISH3'
    batch = Batch('batch1', sku, 100, eta=None)
    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = list(session.execute(
        'SELECT reference, sku, _purchased_quantity, eta FROM batches'
    ))
    assert rows == [('batch1', sku, 100, None)]


def test_respository_can_save_product(session):
    sku = 'COLHER-PAU'
    product = Product(sku, [])
    repo = repository.ProductSqlAlchemyRepository(session)
    repo.add(product)
    session.commit()

    rows = list(session.execute(
        'SELECT sku FROM products WHERE sku=:sku',
        dict(sku=sku)
    ))
    assert rows == [(sku,)]

def test_respository_can_save_product_and_batches(session):
    sku = 'GARFO-PAU'
    batch1 = Batch('batch1', sku, 100, eta=None)
    batch2 = Batch('batch2', sku, 100, eta=None)
    product = Product(sku, [batch1, batch2])
    repo = repository.ProductSqlAlchemyRepository(session)
    repo.add(product)
    session.commit()

    repo = repository.ProductSqlAlchemyRepository(session)
    retrieved = repo.get(sku=sku)

    expected = Product(sku, [batch1, batch2])
    assert retrieved == expected  # batch.__eq__ only compares reference
    assert retrieved.sku == expected.sku
    assert retrieved.batches == [
        Batch('batch1', sku, 100, eta=None),
        Batch('batch2', sku, 100, eta=None),
    ]


def insert_order_line(session):
    session.execute('INSERT INTO order_lines (orderid, sku, qty) '
                    'VALUES ("order1", "GENERIC-SOFA", 12)')
    [[order_line_id]] = session.execute(
        'SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku',
        dict(orderid='order1', sku='GENERIC-SOFA')
    )
    return order_line_id


def insert_batch(session, batch_id):
    session.execute('INSERT INTO batches (reference, sku, _purchased_quantity, eta)'
                    'VALUES (:batch_id, "GENERIC-SOFA", 100, null)',
                    dict(batch_id=batch_id))
    [[batch_id]] = session.execute(
        'SELECT id FROM batches WHERE reference=:batch_id AND sku=:sku',
        dict(batch_id=batch_id, sku='GENERIC-SOFA')
    )

    return batch_id


def insert_allocation(session, orderline_id, batch_id):
    session.execute('INSERT INTO allocations (batch_id, orderline_id)'
                    'VALUES (:batch_id, :orderline_id)',
                    dict(batch_id=batch_id, orderline_id=orderline_id))





def insert_product(session, sku):
    session.execute('INSERT INTO products (sku)'
                    'VALUES (:sku)',
                    dict(sku=sku))
    [[sku]] = session.execute(
        'SELECT sku FROM products WHERE sku=:sku',
        dict(sku=sku)
    )
    return sku