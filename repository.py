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


class SqlRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def _fetch_batch(self, ref: str, sku: str) -> List:
        return list(
            self.session.execute(
                """
            SELECT id FROM `batches`
            WHERE reference = :reference and sku = :sku
            """,
                dict(reference=ref, sku=sku),
            )
        )

    def _insert_batch(self, batch: model.Batch):
        self.session.execute(
            """
            INSERT INTO `batches` (reference, sku, _purchased_quantity, eta)
            VALUES (:reference, :sku, :_purchased_quantity, :eta)
            """,
            dict(
                reference=batch.reference,
                sku=batch.sku,
                _purchased_quantity=batch.purchased_quantity,
                eta=batch.eta,
            ),
        )

    def _insert_order_line(self, order_line: model.OrderLine):
        self.session.execute(
            """
            INSERT INTO `order_lines` (sku, qty, orderid)
            VALUES (:sku, :qty, :orderid)
            """,
            dict(sku=order_line.sku, qty=order_line.qty, orderid=order_line.orderid),
        )

    def _fetch_order_line(self, sku: str, orderid: str) -> List:
        return list(
            self.session.execute(
                """
            SELECT id FROM `order_lines`
            WHERE sku = :sku and orderid = :orderid
            """,
                dict(sku=sku, orderid=orderid),
            )
        )

    def _insert_allocations(self, orderline_id: int, batch_id: int):
        self.session.execute(
            """
            INSERT INTO `allocations` (orderline_id, batch_id)
            VALUES (:orderline_id, :batch_id)
            """,
            dict(orderline_id=orderline_id, batch_id=batch_id),
        )

    def add(self, batch: model.Batch):
        if not self._fetch_batch(batch.reference, batch.sku):
            self._insert_batch(batch)

        [[batch_id]] = self._fetch_batch(batch.reference, batch.sku)
        for order_line in batch.allocations:
            if not self._fetch_order_line(order_line.sku, order_line.orderid):
                self._insert_order_line(order_line)
                [[orderline_id]] = self._fetch_order_line(
                    order_line.sku, order_line.orderid
                )
                self._insert_allocations(orderline_id, batch_id)

    def get(self, reference: str) -> model.Batch:
        data = list(
            self.session.execute(
                """
                SELECT
                    batches.reference,
                    batches.sku,
                    batches._purchased_quantity,
                    batches.eta,
                    order_lines.orderid,
                    order_lines.qty
                FROM batches
                JOIN allocations ON allocations.batch_id = batches.id
                JOIN order_lines ON allocations.orderline_id = order_lines.id
                WHERE reference = :reference
                """,
                dict(reference=reference),
            )
        )
        batch = None
        for ref, sku, _purchased_quantity, eta, orderid, qty in data:
            batch = (
                model.Batch(ref, sku, _purchased_quantity, eta)
                if batch is None
                else batch
            )
            order_line = model.OrderLine(orderid, sku, qty)
            batch.allocate(order_line)
        return batch
