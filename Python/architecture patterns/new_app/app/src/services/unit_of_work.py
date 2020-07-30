# This import is to allow use on __enter__ the instance of own class
from __future__ import annotations

import abc
from sqlalchemy.orm import sessionmaker

import config
from adapters import repository

"""
A unit of work is used, in this case, to set a AbstractRepository and Session of ORM
which in this case a SqlAlchemyUnitOfWork that is responsible to make a connection with 
the real data base    
"""


class AbstractUnitOfWork(abc.ABC):
    products: repository.ProductSqlAlchemyRepository

    def __enter__(self) -> AbstractUnitOfWork:
        return self

    def __exit__(self, *args):
        self.rollback()

    def commit(self):
        self._commit()

    def collect_new_events(self):
        for product in self.products.seen:
            if hasattr(product, 'events'):
                while product.events:
                    yield product.events.pop(0)

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


DEFAULT_SESSION_FACTORY = sessionmaker(bind=config.get_postgres_engine())


class ProductSqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    The module defines a default session factory that will connect to real data base
    (in this case is sqllite), but we allow that to be overridden in our integraton
    tests so that we can use sqllite in memory instead
    """
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    """
    The __enter__ method is responsible for starting a database
    session and instantiating a real repository that can use that session
    """
    def __enter__(self):
        self.session = self.session_factory()  # type: Session
        # self.batches = repository.SqlAlchemyRepository(self.session)
        self.products = repository.ProductSqlAlchemyRepository(self.session)
        return super().__enter__()

    """
    The __enter__ and __exit__ are the two magic methods that execute when we enter
    the "with" block and when we exit i, respectively. They are out setup and teardown phases
    """
    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def _commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

