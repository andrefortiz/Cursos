import json
import logging
import redis

import config
from adapters import orm
from domains import commands
from services import unit_of_work
from services.messagebus import MessageBus

r = redis.Redis(**config.get_redis_host_and_port())

# logger = logging.getLogger(__name__)
logging.basicConfig(filename='example.log', level=logging.INFO)

def main():
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)

    pubsub.subscribe('line_allocated')
    logging.info(" message:" + str(pubsub.get_message()))

    for m in pubsub.listen():
        handle_change_batch_quantity(m)


def handle_change_batch_quantity(m):
    try:
        logging.info('handling %s', m)
        print('handling %s', m)
        data = json.loads(m['data'])

        cmd = commands.ChangeBatchQuantity(ref=data['batchref'], qty=data['qty'])

        MessageBus().handle(cmd, uow=unit_of_work.ProductSqlAlchemyUnitOfWork())
    except Exception as e:
        logging.info(str(e))
        return None


if __name__ == '__main__':
    main()
