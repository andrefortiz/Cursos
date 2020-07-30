from datetime import date

import pytest
from sqlalchemy.orm import clear_mappers

import bootstrap
import views
from domains import commands
from new_app.app.tests.random_def import random_orderid, random_sku, random_batchref
from services import unit_of_work

today = date.today()


@pytest.fixture
def sqlite_bus(sqlite_session_factory):
    bus = bootstrap.bootstrap(start_orm=True,
                              uow=unit_of_work.ProductSqlAlchemyUnitOfWork(sqlite_session_factory),
                              send_mail=lambda *args: None,
                              publish=lambda *args: None, )
    yield bus
    clear_mappers


def test_allocations_view(sqlite_bus):

    orderid1 = random_orderid('1')
    other_orderid1 = random_orderid('other-1')
    sku1, sku2 = random_sku('1'), random_sku('2')

    batch1, batch2, other_batch1 = random_batchref('1'), random_batchref('2'),  random_batchref('other-1')
    sqlite_bus.handle(commands.CreateBatch(batch1, sku1, 50, None))
    sqlite_bus.handle(commands.CreateBatch(batch2, sku2, 50, None))
    sqlite_bus.handle(commands.Allocate(orderid1, sku1, 20))
    sqlite_bus.handle(commands.Allocate(orderid1, sku2, 20))

    sqlite_bus.handle(commands.CreateBatch(other_batch1, sku1, 50, today))

    sqlite_bus.handle(commands.Allocate(other_orderid1, sku1, 30))
    sqlite_bus.handle(commands.Allocate(other_orderid1, sku2, 10))

    assert views.allocations(orderid1, sqlite_bus.uow) == [
        { 'sku': sku1, 'batchref': batch1},
        { 'sku': sku2, 'batchref': batch2},
    ]

"""
def test_allocations_view(session_factory):
    messagebus = MessageBus()
    uow = unit_of_work.ProductSqlAlchemyUnitOfWork(session_factory)

    orderid1 = random_orderid('1')
    other_orderid1 = random_orderid('other-1')
    sku1, sku2 = random_sku('1'), random_sku('2')

    batch1, batch2, other_batch1 = random_batchref('1'), random_batchref('2'),  random_batchref('other-1')
    messagebus.handle(commands.CreateBatch(batch1, sku1, 50, None), uow)
    messagebus.handle(commands.CreateBatch(batch2, sku2, 50, None), uow)
    messagebus.handle(commands.Allocate(orderid1, sku1, 20), uow)
    messagebus.handle(commands.Allocate(orderid1, sku2, 20), uow)

    messagebus.handle(commands.CreateBatch(other_batch1, sku1, 50, today), uow)

    messagebus.handle(commands.Allocate(other_orderid1, sku1, 30), uow)
    messagebus.handle(commands.Allocate(other_orderid1, sku2, 10), uow)

    assert views.allocations(orderid1, uow) == [
        { 'sku': sku1, 'batchref': batch1},
        { 'sku': sku2, 'batchref': batch2},
    ]
"""