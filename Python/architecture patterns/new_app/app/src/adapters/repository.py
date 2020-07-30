import abc

from adapters import orm
from domains.model import Batch, Product, OrderLine

import logging

logging.basicConfig(filename='example.log', level=logging.INFO)

class AbstractRepository(abc.ABC):
    def __init__(self):
        self.seen = set()  # type: Set[model.product]

    def add(self, model):
        raise NotImplementedError

    def get(self, reference):
        raise NotImplementedError

    @abc.abstractmethod
    def _add(self, model):
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, reference):
        raise NotImplementedError


class ProductSqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def add(self, model: Product):
        self._add(model)
        self.seen.add(model)

    def get(self, sku) -> Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batchref(self, reference) -> Product:
        product = self._get_by_batchref(reference)
        if product:
            logging.info('achou o produto: ' + product.sku)
            self.seen.add(product)
        else:
            logging.info('não achou o produto: %s pra referencia: %s', str(product), reference)
        return product

    def _add(self, model: Product):
        self.session.add(model)

    def _get(self, sku) -> Product:
        return self.session.query(Product).filter_by(sku=sku).first()

    def list_batches(self) -> Batch:
        return self.session.query(Batch).all()

    def list_order_lines(self) -> OrderLine:
        return self.session.query(OrderLine).all()

    def _get_by_batchref(self, reference) -> Product:
        return self.session.query(Product).join(Batch).filter(
            orm.batches.c.reference == reference
        ).first()

    def list(self):
        return self.session.query(Product).all()


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def add(self, model: Batch):
        self._add(model)
        self.seen.add(model)

    def get(self, reference) -> Batch:
        batch = self._get(reference)
        if batch:
            self.seen.add(batch)
        return batch

    def _add(self, model: Batch):
        self.session.add(model)

    def _get(self, reference) -> Batch:
        return self.session.query(Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(Batch).all()