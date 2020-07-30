from dataclasses import dataclass
from datetime import date
from typing import Optional, NewType, List

from domains import events, commands

Quantity = NewType("Quantity", int)
Sku = NewType("Sku", str)
Reference = NewType("Reference", str)

import logging
logging.basicConfig(filename='example.log', level=logging.INFO)

class OutOfStock(Exception):
    pass


@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    __clause_element__ = "Product.sku==Batch.sku"

    def __init__(self,
                 ref: Reference, sku: Sku, qty: Quantity, eta: Optional[date]):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()   # type: Set[OrderLine]

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)
            print(' available: ' + str(self.available_quantity))

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)
            print(' sku: ' + line.sku)
            print(' batchref: ' + self.reference)
            print(' available: ' + str(self.available_quantity))

    def deallocate_one(self) -> OrderLine:
        return self._allocations.pop()

    @property
    def allocate_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocate_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and \
               self.available_quantity >= line.qty

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    @property
    def orderids(self):
        return {l.orderid for l in self._allocations}


class Product:

    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events = []  # type: List[events.Event]
        self.commands = []  # type: List[commands.Command]

    def get_batch(self, reference):
        if len(self.batches) > 0:
            return next(b for b in self.batches if b.reference == reference)
        return None

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1

            if not hasattr(self, 'events'):
                self.events = []

            self.events.append(events.Allocated(
                orderid=line.orderid, sku=line.sku, qty=line.qty, batchref=batch.reference
            ))

            return batch.reference
        except StopIteration as e:
            # This is the first example of raise an event
            if not hasattr(self, 'events'):
                self.events = []
            self.events.append(events.OutOfStock(line.sku))
            return e

    def change_batch_quantity(self, ref: str, qty: int):
        batch = next(b for b in self.batches if b.reference == ref)
        batch._purchased_quantity = qty
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            logging.info('desalocou ')
            if not hasattr(self, 'events'):
                self.events = []
            self.events.append(commands.Allocate(line.orderid, line.sku, line.qty))

    def __eq__(self, other):
        if not isinstance(other, Product):
            return False
        return other.sku == self.sku

    def __hash__(self):
        return hash(self.sku)