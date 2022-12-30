from __future__ import annotations

from datetime import date
from typing import Optional

import model
from model import Batch, OrderLine
from repository import AbstractRepository


class InvalidSku(Exception):
    pass


class DoNotExist(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batchref = model.allocate(line, batches)
    session.commit()
    return batchref


def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[date], repo: AbstractRepository, session
):
    batch = Batch(ref, sku, qty, eta)
    repo.add(batch)
    session.commit()


def deallocate(orderid: str, sku: str, repo: AbstractRepository, session) -> str:
    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSku(f"Invalid sku {sku}")
    try:
        order_line = repo.get_order_line(orderid, sku)
    except StopIteration:
        raise DoNotExist(f"{orderid} does not Exist")
    batchref = model.deallocate(order_line, batches)
    session.commit()
    return batchref
