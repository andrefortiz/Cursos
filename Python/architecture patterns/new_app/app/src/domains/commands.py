import json
from dataclasses import dataclass, make_dataclass
from datetime import date
from typing import Optional

from schema import Schema, And, Use

def greater_than_zero(x):
    return x > 0


quantity = And(Use(int), greater_than_zero)

class Command:
    pass


@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: quantity

    """
    @classmethod
    def from_json(cls, data):
        _schema = Schema({
            'orderid': str,
            'sku': str,
            'qty': And(Use(int), lambda n: n > 0)
        }, ignore_extra_keys=True)

        #data = json.loads(data)
        return cls(**_schema.validate(data))
    """

@dataclass
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None


@dataclass
class ChangeBatchQuantity(Command):
    ref: str
    qty: int


@dataclass
class GetBaches(Command):
    ref: str

@dataclass
class GetProductByRef(Command):
    ref: str

@dataclass
class GetProducts(Command):
    sku: str

@dataclass
class GetOrderLines(Command):
    sku: str


def command(name, **fields):
    schema = Schema(And(Use(json.loads), fields), ignore_extra_keys=True)
    cls = make_dataclass(name, fields.keys())
    cls.from_json = lambda s: cls(**schema.validate(s))
    return cls


Allocate = command(name='Allocate',
    orderid=int,
    sku=str,
    qty=quantity
)
