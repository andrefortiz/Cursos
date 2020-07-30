from datetime import date, timedelta
from typing import Optional

import pytest

from domains import model, events
from services import unit_of_work, handlers
from services.messagebus import HANDLERS

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)

class FakeMessageBus:

    @staticmethod
    def handle(event: events.Event):
        for handler in HANDLERS[type(event)]:
            handler(event)

    @staticmethod
    def send_out_of_stock_notification(event: events.OutOfStock):
        print(f'Out of stock for {event.sku}')


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self, repo: Optional[any]):
        # self.batches = FakeRepository([])
        if repo is not None:
            self.products = repo
        else:
            self.products = FakeProductRepository([])
        self.committed = False

    def commit(self):
        self.committed = True
        self.publish_events()

    def publish_events(self):
        for product in self.products.seen:
            while product.events:
                event = product.events.pop(0)
                FakeMessageBus.handle(event)

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeRepository(set):
    """
    Metodo usado pra adicionar o objeto "batch" já
    com om modelo na "memória" e retonar o repositorio
    """
    @staticmethod
    def for_batch(ref, sku, qty, eta=None):
        return FakeRepository(
            model.Batch(ref, sku, qty, eta))

    def __init__(self, batches):
        super().__init__()
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


class FakeProductRepository(set):
    """
    Metodo usado pra adicionar o objeto "batch" já
    com om modelo na "memória" e retonar o repositorio
    """
    @staticmethod
    def for_batch(ref, sku, qty, eta=None):
        return FakeProductRepository([
            model.Product(sku, batches=[model.Batch(ref, sku, qty, eta)])
        ])

    def __init__(self, products):
        self.seen = set()  # type: Set[model.product]
        self.products = set(products)

    def add(self, product):
        self._add(product)
        self.seen.add(product)

    def get(self, sku):
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def _add(self, product):
        self.products.add(product)

    def _get(self, sku):
        try:
            if len(self.products) > 0:
                return next(b for b in self.products if b.sku == sku)
            return None
        except StopIteration as e:
            return e.value

    def list(self):
        return list(self.products)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_add_batch():
    batch = 'b1'
    sku = 'CRUNCHY-ARMCHAIR'

    uow = FakeUnitOfWork(None)
    handlers.add_batch(batch, sku, 100, None, uow)
    assert uow.products.get(sku=sku).get_batch(batch) is not None
    assert uow.committed


def test_prefers_warehouse_batches_to_shipments():
    sku = 'RETRO-CLOCK'
    in_stock_batch = 'in-stock-batch'
    shipment_batch = 'shipment-batch'

    uow = FakeUnitOfWork(None)
    handlers.add_batch(in_stock_batch, sku, 100, None, uow)
    handlers.add_batch(shipment_batch, sku, 100, tomorrow, uow)

    handlers.allocate('oref', sku, 10, uow)
    product = uow.products.get(sku=sku)
    assert product.get_batch(in_stock_batch).available_quantity == 90
    assert product.get_batch(shipment_batch).available_quantity == 100


def test_records_out_of_stock_event_if_cannot_allocate():
    sku = 'RETRO-CLOCK'
    in_stock_batch = 'in-stock-batch'

    uow = FakeUnitOfWork(None)
    handlers.add_batch(in_stock_batch, sku, 10, None, uow)

    allocation = handlers.allocate('oref', sku, 11, uow)
    product = uow.products.get(sku=sku)

    # assert product.events[-1] == events.OutOfStock(sku=sku)
    assert allocation is None


def test_returns_allocation():
    uow = FakeUnitOfWork(
        FakeProductRepository.for_batch('b1', 'COMPLICATED-LAMP', 100, eta=None))

    result = handlers.allocate('o1', 'COMPLICATED-LAMP', 10, uow)
    assert result == 'b1'


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork(
        FakeProductRepository.for_batch('b1', 'COMPLICATED-LAMP', 100, eta=None))
    handlers.add_batch('b1', 'COMPLICATED-LAMP', 100, None, uow)

    result = handlers.allocate('o1', 'COMPLICATED-LAMP', 10, uow)
    assert result == 'b1'


def test_error_for_invalid_sku():
    uow = FakeUnitOfWork(None)
    handlers.add_batch('b1', 'AREALSKU', 100, None, uow)

    with pytest.raises(handlers.InvalidSku, match='Invalid sku NONEXISTENTSKU'):
        handlers.allocate('o1', 'NONEXISTENTSKU', 10, uow)


def test_commits():
    uow = FakeUnitOfWork(None)
    handlers.add_batch('b1', 'OMINOUS-MIRROR', 100, None, uow)

    handlers.allocate('o1', 'OMINOUS-MIRROR', 10, uow)
    assert uow.committed is True


"""

def test_prefers_warehouse_batches_to_shipments():
    in_stock_batch = Batch('in-stock-batch', 'RETRO-CLOCK', 100, eta=None)
    shipment_batch = Batch('shipment-batch', 'RETRO-CLOCK', 100, eta=tomorrow)

    repo = FakeRepository([in_stock_batch, shipment_batch])
    session = FakeSession()

    services.allocate('oref', 'RETRO-CLOCK', 10, repo, session)
    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_returns_allocation():
    repo = FakeRepository.for_batch('b1', 'COMPLICATED-LAMP', 100, eta=None)

    result = services.allocate('o1', 'COMPLICATED-LAMP', 10, repo, FakeSession())
    assert result == 'b1'


def test_allocate_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch('b1', 'COMPLICATED-LAMP', 100, None, repo, session)

    result = services.allocate('o1', 'COMPLICATED-LAMP', 10, repo, FakeSession())
    assert result == 'b1'


def test_allocate_errors_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()

    services.add_batch('b1', 'AREALSKU', 100, None, repo, session)
    with pytest.raises(services.InvalidSku, match='Invalid sku NONEXISTENTSKU'):
        services.allocate('o1', 'NONEXISTENTSKU', 10, repo, FakeSession())


def test_error_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch('b1', 'AREALSKU', 100, None, repo, session)

    with pytest.raises(services.InvalidSku, match='Invalid sku NONEXISTENTSKU'):
        services.allocate('o1', 'NONEXISTENTSKU', 10, repo, FakeSession())

"""