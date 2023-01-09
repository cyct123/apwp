from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Type

from src.allocation.domain import events

from . import handlers

if TYPE_CHECKING:
    from . import unit_of_work


class AdstractMessageBus:
    HANDLERS: Dict[Type[events.Event], List[Callable]]

    def handle(self, event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
        results = []
        queue = [event]
        while queue:
            event = queue.pop(0)
            for handler in self.HANDLERS[type(event)]:
                results.append(handler(event, uow))
                queue.extend(uow.collect_new_events())
        return results


class MessageBus(AdstractMessageBus):
    HANDLERS = {
        events.BatchCreated: [handlers.add_batch],
        events.BatchQuantityChanged: [handlers.change_batch_quantity],
        events.AllocationRequired: [handlers.allocate],
        events.OutOfStock: [handlers.send_out_of_stock_notification],
    }  # type: Dict[Type[events.Event], List[Callable]]


messagebus = MessageBus()
