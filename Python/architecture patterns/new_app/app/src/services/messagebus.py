import logging
from typing import Dict, Type, List, Callable, Union

from tenacity import Retrying, stop_after_attempt, wait_exponential, RetryError

from domains import events, commands
from services import unit_of_work

# logger = logging.getLogger(__name__)
logging.basicConfig(filename='example.log', level=logging.INFO)


class AbstractMessageBus:
    EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]]
    COMMAND_HANDLERS: Dict[Type[commands.Command], Callable]


class MessageBus(AbstractMessageBus):
    Message = Union[commands.Command, events.Event]

    def __init__(self,
                 uow: unit_of_work.AbstractUnitOfWork,
                 event_handlers: Dict[Type[events.Event], List[Callable]],
                 command_handlers: Dict[Type[commands.Command], Callable]):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    def handle(self, message: Message):
        results = []
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):
                result = self.handle_command(message)
                results.append(result)
            else:
                raise Exception(f'{message} was not an Event or Command')

        return results

    def handle_event(self, event: events.Event):
        for handler in self.event_handlers[type(event)]:
            try:
                for attempt in Retrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential()
                ):
                    with attempt:
                        logging.info('handling event %s with handler %s', event, handler)
                        handler(event)
                        self.queue.extend(self.uow.collect_new_events())

            except RetryError as retry_failure:
                logging.info('Failed to handle event %s times, givin up!',
                             retry_failure.last_attempt.attempt_number)
                continue

    def handle_command(self, command: commands.Command):
        logging.info('handling command %s', command)
        try:
            handler = self.command_handlers[type(command)]
            result = handler(command)
            self.queue.extend(self.uow.collect_new_events())
            return result
        except Exception as e:
            logging.info('Exception handling command', str(e))
            raise

    """
    @staticmethod
    def send_out_of_stock_notification(event: events.OutOfStock):
        # email.send_mail('teste@teste.com.br', f'Out of stock for {event.sku}')
        print(f'Out of stock for {event.sku}')
    """

