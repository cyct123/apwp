from dataclasses import dataclass
from datetime import date
from typing import Optional, List, Set


class OutOfStock(Exception):
    pass

@dataclass(frozen=True)
class OrderLine:
    orderId: str
    sku: str
    orderQuantity: int


class Batch:

    def __init__(self, ref: str, sku: str, quantity: int, eta: Optional[date]):
        self.reference = ref
        self.sku = sku
        self._purchased_quantity = quantity
        self.eta = eta
        self._allocations: Set[OrderLine] = set()

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return self.reference == other.reference

    def __hash__(self):
        return hash(self.reference)

    def __lt__(self, other):
        if self.eta is None:
            return True
        if other.eta is None:
            return False
        return self.eta < other.eta

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    @property
    def allocated_quantity(self):
        return sum(line.orderQuantity for line in self._allocations)

    @property
    def available_quantity(self):
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine):
        return self.sku == line.sku and self.available_quantity >= line.orderQuantity

def allocate(line: OrderLine, batches: List[Batch]):
    try:
        batch = next(batch for batch in sorted(batches) if batch.can_allocate(line))
    except StopIteration:
        raise OutOfStock()
    batch.allocate(line)
