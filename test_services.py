import pytest

import model
import repository
import services
from services import DoNotExist, InvalidSku


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)

    def get_order_line(self, orderid, sku) -> model.OrderLine:
        return next(
            line
            for b in self._batches
            for line in b.allocations
            if line.orderid == orderid and line.sku == sku
        )


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_returns_allocation():
    line = model.OrderLine("o1", "COMPLICATED-LAMP", 10)
    batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())
    assert result == "b1"


def test_error_for_invalid_sku():
    line = model.OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate(line, repo, FakeSession())


def test_commits():
    line = model.OrderLine("o1", "OMINOUS-MIRROR", 10)
    batch = model.Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(line, repo, session)
    assert session.committed is True


def test_deallocate_decrements_available_quantity():
    repo, session = FakeRepository([]), FakeSession()
    # TODO: you'll need to implement the services.add_batch method
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    line = model.OrderLine("o1", "BLUE-PLINTH", 10)
    services.allocate(line, repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90
    services.deallocate("o1", "BLUE-PLINTH", repo, session)
    assert batch.available_quantity == 100


def test_deallocate_decrements_correct_quantity():
    #  TODO - check that we decrement the right sku
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    line = model.OrderLine("o1", "BLUE-PLINTH", 10)
    services.allocate(line, repo, session)
    with pytest.raises(InvalidSku, match="WHITE-PLINTH"):
        services.deallocate("o1", "WHITE-PLINTH", repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90


def test_trying_to_deallocate_unallocated_batch():
    #  TODO: should this error or pass silently? up to you.
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    with pytest.raises(DoNotExist, match="o1"):
        services.deallocate("o1", "BLUE-PLINTH", repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 100
