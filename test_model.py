from datetime import date, timedelta

from model import OrderLine, Batch, allocate

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_allocating_to_a_batch_reduces_the_available_quantity():
    line = OrderLine("123", "test", 2)
    batch = Batch("234", "test", 20, None)
    batch.allocate(line)
    assert batch.available_quantity == 18


def test_can_allocate_if_available_greater_than_required():
    line = OrderLine("123", "test", 2)
    batch = Batch("234", "test", 20, None)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_available_smaller_than_required():
    line = OrderLine("123", "test", 2)
    batch = Batch("234", "test", 1, None)
    assert not batch.can_allocate(line)


def test_can_allocate_if_available_equal_to_required():
    line = OrderLine("123", "test", 2)
    batch = Batch("234", "test", 2, None)
    assert batch.can_allocate(line)


def test_prefers_warehouse_batches_to_shipments():
    line = OrderLine("123", "test", 2)
    warehouse_batch = Batch("234", "test", 20, None)
    shipment_batch = Batch("123", "test", 20, date(2022, 12,10))
    allocate(line, [warehouse_batch, shipment_batch])
    assert warehouse_batch.available_quantity == 18
    assert shipment_batch.available_quantity == 20


def test_prefers_earlier_batches():
    line = OrderLine("123", "test", 2)
    earlier_batch = Batch("234", "test", 20, date(2022, 12, 1))
    later_batch = Batch("123", "test", 20, date(2022, 12,10))
    allocate(line, [earlier_batch, later_batch])
    assert earlier_batch.available_quantity == 18
    assert later_batch.available_quantity == 20
