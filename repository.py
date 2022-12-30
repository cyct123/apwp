import abc
from typing import List

import model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> List[model.Batch]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_order_line(self, orderid, sku) -> model.OrderLine:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(model.Batch).all()

    def get_order_line(self, orderid, sku) -> model.OrderLine:
        return (
            self.session.query(model.OrderLine)
            .filter_by(orderid=orderid, sku=sku)
            .one()
        )
