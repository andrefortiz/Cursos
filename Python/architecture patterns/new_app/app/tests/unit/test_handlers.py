from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

import pytest
from sqlalchemy.orm import clear_mappers

import bootstrap
from adapters.notifications import AbstractNotifications
from domains import model, events, commands
from services import unit_of_work
from services.messagebus import MessageBus, AbstractMessageBus

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


class FakeNotifications(AbstractNotifications):
    def __init__(self):
        self.sent = defaultdict(list)  # type: Dict[str. List[str]]

    def send(self, destination, message):
        self.sent[destination].append(message)
        print(f'enviando email: {message} para {destination}')


class FakeMessageBus(AbstractMessageBus):

    def __init__(self):
        self.events_published = []  # type: List[events.Event]
        self.handlers = {
            events.OutOfStock: [lambda e: self.events_published.append(e)]
        }

    def handle(self, event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
        self.events_published.append(event)


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

    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeUnitOfWorkWithFakeMessageBus(FakeUnitOfWork):
    def __init__(self):
        super().__init__(None)
        self.events_published = []  # type: List[events.Event]

    def publish_events(self):
        for product in self.products.seen:
            while product.events:
                self.events_published.append(product.events.pop(0))


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

    def get_by_batchref(self, reference):
        product = self._get_by_batchref(reference)
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

    def _get_by_batchref(self, reference):
        try:
            if len(self.products) > 0:
                return next(p for p in self.products for b in p.batches if b.reference == reference)
            return None
        except StopIteration as e:
            return e.value

    def list(self):
        return list(self.products)

class FakeNotifications:
    def send(self, destination, message):
        print(f'destination: {destination}')
        print(f'message: {message}')


@pytest.fixture
def fake_bus():
    bus = bootstrap.bootstrap(start_orm=False,
                              uow=FakeUnitOfWork(None),
                              notifications=FakeNotifications(),
                              publish=lambda *args: None, )
    yield bus
    clear_mappers


class TestAddBatch:

    def test_for_new_product(self, fake_bus):
        batch = 'b1'
        sku = 'CRUNCHY-ARMCHAIR'

        #uow = FakeUnitOfWork(None)
        #MessageBus().handle(commands.CreateBatch(batch, sku, 100, None), uow)
        fake_bus.handle(commands.CreateBatch(batch, sku, 100, None))
        assert fake_bus.uow.products.get(sku=sku).get_batch(batch) is not None
        assert fake_bus.uow.committed


class TestAllocate:

    def test_returns_allocation(self, fake_bus):
        batch = 'b1'
        sku = 'COMPLICATED-LAMP'

        #uow = FakeUnitOfWork(None)
        #MessageBus().handle(commands.CreateBatch(batch, sku, 100, None), uow)
        #result = MessageBus().handle(commands.Allocate('o1', sku, 10), uow)
        fake_bus.handle(commands.CreateBatch(batch, sku, 100, None))
        result = fake_bus.handle(commands.Allocate('o1', sku, 0))
        assert result == [batch]


class TestChangeBatchQuantity:
    def test_changes_available_quantity(self):
        batchref = 'b1'
        sku = 'COMPLICATED-LAMP'

        uow = FakeUnitOfWork(None)
        MessageBus().handle(commands.CreateBatch(batchref, sku, 100, None), uow)

        [batch] = uow.products.get(sku=sku).batches
        assert batch.available_quantity == 100

        MessageBus().handle(commands.ChangeBatchQuantity(batchref, 50), uow)
        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        batchref1 = 'b1'
        batchref2 = 'b2'
        sku = 'FACA-DOISGUMES'

        uow = FakeUnitOfWork(None)
        event_history = [
            commands.CreateBatch(batchref1, sku, 50, None),
            commands.CreateBatch(batchref2, sku, 50, date.today()),
            commands.Allocate('o1', sku, 21),
            commands.Allocate('o2', sku, 20),
        ]

        for e in event_history:
            MessageBus().handle(e, uow)

        [batch1, batch2] = uow.products.get(sku=sku).batches
        assert batch1.available_quantity == 9
        assert batch2.available_quantity == 50

        MessageBus().handle(commands.ChangeBatchQuantity(batchref1, 25), uow)
        # order1 or order2 will be deallocated, so we'll have 25 - 21
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 29


def test_sends_email_on_out_of_stock_error():
    fake_notifs = FakeNotifications()
    bus = bootstrap.bootstrap(
        start_orm=False,
        uow=FakeUnitOfWork(None),
        notifications=fake_notifs,
        publish=lambda *args: None)
    bus.handle(commands.CreateBatch('b1', 'POPULAR-CURTAINS', 9, None))
    bus.handle(commands.Allocate('o1', 'POPULAR-CURTAINS', 10))
    assert fake_notifs.sent['teste@teste.com.br'] == [
        f'Out of stock for POPULAR-CURTAINS',
    ]

def test_reallocates_if_necessary_isolated():
    batchref1 = 'b1'
    batchref2 = 'b2'
    sku = 'FACA-DOISGUMES'

    uow = FakeUnitOfWorkWithFakeMessageBus()
    event_history = [
        events.BatchCreated(batchref1, sku, 50, None),
        events.BatchCreated(batchref2, sku, 50, date.today()),
        events.AllocationRequired('o1', sku, 21),
        events.AllocationRequired('o2', sku, 20),
    ]

    messagebus = FakeMessageBus()
    for e in event_history:
        messagebus.handle(e, uow)

    [batch1, batch2] = uow.products.get(sku=sku).batches
    assert batch1.available_quantity == 9
    assert batch2.available_quantity == 50

    messagebus.handle(events.BatchQuantityChanged(batchref1, 25), uow)
    # assert on new events emitted rather than downstream side-effects
    [reallocation_event] = uow.events_published
    assert isinstance(reallocation_event, events.AllocationRequired)

    assert reallocation_event.orderid in {'o1', 'o2'}
    assert reallocation_event.sku == sku
