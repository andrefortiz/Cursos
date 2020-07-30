import inspect
from collections import Callable

import config
from adapters import orm
from adapters.notifications import AbstractNotifications, EmailNotification
from entrypoints import redis_eventpublisher
from services import unit_of_work, handlers
from services.messagebus import MessageBus


def bootstrap(start_orm: bool = True,
              uow: unit_of_work.AbstractUnitOfWork = unit_of_work.ProductSqlAlchemyUnitOfWork(),
              notifications: AbstractNotifications = EmailNotification(),
              publish: Callable = redis_eventpublisher.publish, ) -> MessageBus:

    if start_orm:
        print('vai gerar a base de dados: ', config.get_postgres_uri())
        orm.start_mappers()

    dependencies = {'uow': uow, 'send_mail': notifications, 'publish': publish}

    inject_event_handlers = {
        event_type: [
            inject_dependencies(handler, dependencies) for handler in event_handlers
        ]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }

    inject_command_handlers = {
        command_type: inject_dependencies(handler, dependencies)
        for command_type, handler in handlers.COMMAND_HANDLERS.items()
    }
    """
    inject_event_handlers = {
        events.Allocated: [
            lambda e: handlers.publish_allocated_event(e, publish),
            lambda e: handlers.add_allocation_to_read_model(e, uow),
        ],
        events.Deallocated: [
            lambda e: handlers.remove_allocation_from_read_model(e, uow),
            lambda e: handlers.reallocate(e, uow),
        ],
        events.OutOfStock: [
            lambda e: handlers.send_out_of_stock_notification(e, send_mail),
        ]
    }

    inject_command_handlers = {
        commands.Allocate: lambda c: handlers.allocate(c, uow),
        commands.CreateBatch: lambda c: handlers.add_batch(c, uow),
        commands.ChangeBatchQuantity: lambda c: handlers.change_batch_quantity(c, uow),
    }
    """

    return MessageBus(
        uow=uow,
        event_handlers=inject_event_handlers,
        command_handlers=inject_command_handlers,
    )


def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency for name, dependency in dependencies.items() if name in params
    }
    return lambda message: handler(message, **deps)



