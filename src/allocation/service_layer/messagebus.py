from typing import Callable, Dict, List, Type

from src.allocation.domain import events

from . import handlers, unit_of_work


class AbstractMessageBus:

    HANDLERS: Dict[Type[events.Event], List[Callable]]

    def handle(self, event: events.Event):
        for handler in self.HANDLERS[type(event)]:
            handler(event)


class MessageBus(AbstractMessageBus):
    HANDLERS = {
        events.OutOfStock: [handlers.send_out_of_stock_notification],
        events.BatchCreated: [handlers.add_batch],
        events.BatchQuantityChanged: [handlers.change_batch_quantity],
        events.AllocationRequired: [handlers.allocate],
    }


def handle(
    event: events.Event,
    uow: unit_of_work.AbstractUnitOfWork,
):
    results = []
    queue = [event]
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            results.append(handler(event, uow=uow))
            queue.extend(uow.collect_new_events())
    return results


HANDLERS = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.BatchCreated: [handlers.add_batch],
    events.BatchQuantityChanged: [handlers.change_batch_quantity],
    events.AllocationRequired: [handlers.allocate],
}  # type: Dict[Type[events.Event], List[Callable]]
