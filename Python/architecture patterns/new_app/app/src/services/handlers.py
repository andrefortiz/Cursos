from dataclasses import asdict

from adapters.notifications import EmailNotification
from domains import model, events, commands
from services import unit_of_work
import logging

logging.basicConfig(filename='example.log', level=logging.INFO)

class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(command: commands.CreateBatch, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku=command.sku)
        if product is None:
            product = model.Product(command.sku, batches=[])
            uow.products.add(product)

        product.batches.append(model.Batch(command.ref, command.sku, command.qty, command.eta))
        uow.commit()


def allocate(command: commands.Allocate, uow: unit_of_work.AbstractUnitOfWork): #-> str:

    line = model.OrderLine(command.orderid, command.sku, command.qty)
    with uow:
        product = uow.products.get(sku=command.sku)
        if product is None:
            raise InvalidSku(f'Invalid sku {line.sku}')
        batchref = product.allocate(line)  # 3
        uow.commit()  # 4
        #tive que comentar o retorno porque qdo uso o sqlite da ero de thread, vou ter q ver pq
        #return batchref


def reallocate(event: events.Deallocated, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku=event.sku)
        product.events.append(commands.Allocate(**asdict(event)))
        uow.commit()


def change_batch_quantity(command: commands.ChangeBatchQuantity, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        try:
            product = uow.products.get_by_batchref(command.ref)

            result = 0
            logging.info('chegou pra alterar a quantidade da remessa')
            if product is not None:
                logging.info('vai alterar o produto :' + product.sku)
                product.change_batch_quantity(command.ref, command.qty)
                result = 1
            uow.commit()
            return result
        except Exception as e:
            logging.info('ocorreu erro: ' + str(e))


def add_allocation_to_read_model(event: events.Allocated, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        logging.info("vai inserir na tabela de leitura: " + str(event))
        uow.session.execute(
            ' INSERT INTO allocations_view (orderid, sku, batchref)'
            ' VALUES (:orderid, :sku, :batchref)',
            dict(orderid=event.orderid, sku=event.sku, batchref=event.batchref)
        )
        uow.commit()


def remove_allocation_from_read_model(event: events.Deallocated, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        logging.info("vai remover na tabela de leitura: " + str(event))
        uow.session.execute(
            ' DELETE FROM allocations_view WHERE orderid = :orderid AND sku = :sku',
            dict(orderid=event.orderid, sku=event.sku)
        )
        uow.commit()


def publish_allocated_event(event: events.Allocated, uow: unit_of_work.AbstractUnitOfWork):
    # redis_eventpublisher.publish('line_allocated', event)
    logging.info("vai publicar o evento line_allocated: " + str(event))
    #redis_eventpublisher.publish('line_allocated', event)


def send_out_of_stock_notification(event: events.OutOfStock, send_mail: EmailNotification):
    destination = 'teste@teste.com.br'
    message = f'Out of stock for {event.sku}'
    # email.send_mail()

    #print(f'Out of stock for {event.sku}')
    send_mail.send(destination, message)
    logging.info("vai enviar email out of stock")



#  testes
def list_batches(command: commands.ChangeBatchQuantity, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        batches = uow.products.list_batches()
        uow.session.expunge_all()
        uow.session.close()
        return batches


def list_products(command: commands.ChangeBatchQuantity, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        products = uow.products.list()
        uow.session.expunge_all()
        uow.session.close()
        return products

def list_order_lines(command: commands.ChangeBatchQuantity, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        order_lines = uow.products.list_order_lines()
        uow.session.expunge_all()
        uow.session.close()
        return order_lines

def get_product_by_batch_ref(command: commands.GetBaches, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batchref(command.ref)
        uow.session.expunge_all()
        uow.session.close()
        return product




"""
def allocate(orderid: str, sku: str, qty:int, repo: AbstractRepository, session) -> str:

    line = model.OrderLine(orderid, sku, qty)
        batches = repo.list() #1
    if not is_valid_sku(line.sku, batches): #2
        raise InvalidSku(f'Invalid sku {line.sku}')
    batchref = model.allocate(line, batches) #3
    session.commit() #4
    return batchref


def allocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> str:

    line = model.OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            raise InvalidSku(f'Invalid sku {line.sku}')
        # This is the first example of raise an event
        # try:
        batchref = product.allocate(line)  # 3
        uow.commit()  # 4

        # This is the second example of raise an evetnt
        # if batchref is None:
            # messagebus.handle(events.OutOfStock(line.sku))

        return batchref
        # This is the first example of raise an event
        # finally:
            # messagebus.handle(product.events)


def add_batch(ref: str, sku: str, qty: int, eta: Optional[date], uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            product = model.Product(sku, batches=[])
            uow.products.add(product)

        product.batches.append(model.Batch(ref, sku, qty, eta))
        uow.commit()
        
"""

EVENT_HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification],
    events.Allocated: [publish_allocated_event,
                       add_allocation_to_read_model],
    events.Deallocated: [remove_allocation_from_read_model,
                         reallocate],
}  # type: Dict[Type[events.Event], List[Callable]]

COMMAND_HANDLERS = {
    commands.CreateBatch: add_batch,
    commands.Allocate: allocate,
    commands.ChangeBatchQuantity: change_batch_quantity,
    commands.GetBaches: list_batches,
    commands.GetProducts: list_products,
    commands.GetOrderLines: list_order_lines,
    commands.GetProductByRef: get_product_by_batch_ref,
}  # type: Dict[Type[commands.Command], Callable]

