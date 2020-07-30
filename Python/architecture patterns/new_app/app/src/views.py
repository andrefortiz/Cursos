from services import unit_of_work


def allocations(orderid: str, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        results = list(uow.session.execute(
            'SELECT sku, batchref FROM allocations_view WHERE orderid = :orderid',
            dict(orderid=orderid)
        ))
    return [dict(r) for r in results]

    """
    with uow:
        batches = uow.session.query(model.Batch).join(
            model.OrderLine, model.Batch._allocations
        ).filter(
            model.OrderLine.orderid == orderid
        )

        return [{'sku': b.sku, 'batchref': b.reference} for b in batches]
    """
    """
    with uow:
        products = uow.products.for_order(orderid=orderid)
        batches = [b for p in products for b in p.batches]
        return [{'sku': b.sku, 'batchref': b.reference} for b in batches if orderid in b.orderids]
    """
    """
    with uow:
        results = list(uow.session.execute(
            'SELECT ol.sku, b.reference'
            '  FROM allocations AS a'
            '  JOIN batches AS b ON a.batch_id = b.id'
            '  JOIN order_lines AS ol ON a.orderline_id = ol.id'
            ' WHERE ol.orderid = :orderid',
            dict(orderid=orderid)
        ))
    return [{'sku': sku, 'batchref': batchref} for sku, batchref in results]
    """