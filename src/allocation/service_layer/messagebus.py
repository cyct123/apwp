from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Dict, List, Type, Union

from tenacity import RetryError, Retrying, stop_after_attempt, wait_exponential

from src.allocation.domain import commands, events

from . import handlers

if TYPE_CHECKING:
    from . import unit_of_work
Message = Union[commands.Command, events.Event]


def handle(
    message: Message,
    uow: unit_of_work.AbstractUnitOfWork,
):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue, uow)
            results.append(cmd_result)
        else:
            raise Exception(f"{message} was not an Event or Command")
    return results


def handle_event(
    event: events.Event, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork
):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(3), wait=wait_exponential()
            ):
                with attempt:
                    logging.debug("handling event %s with handler %s", event, handler)
                    handler(event, uow=uow)
                    queue.extend(uow.collect_new_events())
        except RetryError as retry_failure:
            logging.error(
                "Failef to handle event %s %s times, giving up!",
                event,
                retry_failure.last_attempt.attempt_number,
            )
            continue


def handle_command(
    command: commands.Command,
    queue: List[Message],
    uow: unit_of_work.AbstractUnitOfWork,
):
    logging.debug("handling command %s", command)
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow=uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logging.exception("Exception handling command %s", command)
        raise


EVENT_HANDLERS = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}  # type: Dict[Type[events.Event], List[Callable]]
COMMAND_HANDLERS = {
    commands.CreateBatch: handlers.add_batch,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,
    commands.Allocate: handlers.allocate,
}  # type: Dict[Type[commands.Command], Callable]
