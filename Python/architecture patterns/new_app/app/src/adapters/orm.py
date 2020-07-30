from sqlalchemy import (
    Table, MetaData, Column, Integer, String, Date,
    ForeignKey
)
from sqlalchemy.orm import mapper, relationship

from domains.model import OrderLine, Batch, Product

metadata = MetaData()

order_lines = Table(
    'order_lines', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('sku', String(255)),
    Column('qty', Integer, nullable=False),
    Column('orderid', String(255)),
)

batches = Table(
    'batches', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('reference', String(255)),
    Column('sku', ForeignKey('products.sku')),
    Column('_purchased_quantity', Integer, nullable=False),
    Column('eta', Date, nullable=True),
)

allocations = Table(
    'allocations', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('orderline_id', ForeignKey('order_lines.id')),
    Column('batch_id', ForeignKey('batches.id')),
)

products = Table(
    'products', metadata,
    Column('sku', String(255), primary_key=True),
    Column('version_number', Integer)
)

allocations_view = Table(
    'allocations_view', metadata,
    Column('orderid', String(255)),
    Column('sku', String(255)),
    Column('batchref', String(255)),
)

def start_mappers():
    """
    lines_mapper = mapper(OrderLine, order_lines)
    mapper(Batch, batches, properties={
        '_allocations': relationship(
            lines_mapper,
            secondary=allocations,
            collection_class=set,
        )
    })
    """
    lines_mapper = mapper(OrderLine, order_lines)
    batch_mapper = mapper(Batch, batches, properties={
        '_allocations': relationship(
            lines_mpapper,
            secondary=allocations,
            collection_class=set,
        ),
    })

    mapper(Product, products, properties={
        'batches':  relationship(
            batch_mapper
        ),
    })
