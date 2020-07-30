import json
import os

import pytest

from adapters import orm
from new_app.app.tests.e2e import api_client, redis_client
from tenacity import Retrying, stop_after_delay
from new_app.app.tests.random_def import random_sku, random_batchref, random_orderid
from entrypoints import redis_eventconsumer

#import logging

#logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def test_publish():


    orderid, sku = random_orderid(), random_sku()

    earlier_batch, later_batch = random_batchref('newer'), random_batchref('old')

    api_client.post_to_add_batch(earlier_batch, sku, qty=10, eta='2011-01-02', local=True)

    api_client.post_to_add_batch(later_batch, sku, qty=10, eta='2011-01-03', local=True)

    response = api_client.post_to_allocate(orderid, sku, 10, local=True)
    print('old_batch: ' + later_batch)
    print('newer_batch: ' + earlier_batch)
    assert response.json()['batchref'] == earlier_batch
    r = api_client.post_list_batches(earlier_batch, local=True)
    print(r.text)


    data = json.dumps({
        "data": "{ \"batchref\": \"batch-newer-cdb516\", \"qty\": 5 }"
    })

    #NECESSARIO MAPPEAR A BASE PARA CONSEGUIR EXECUTAR A QUERY PQ SOMENTE
    #PELO sessionmaker(bind=config.get_sqlite_engine()) DA CAMADA UNIT_OF_WORK
    #NÃO É POSSÍVEL POIS ELE NÃO FAZ O MAPEAMENTO, NO CASO DA API É FEITA NA PRIMEIRA EXECUÇÃO DO FLASK
    orm.start_mappers()
    retorno = redis_eventconsumer.handle_change_batch_quantity(json.loads(data))
    print(retorno)

# @pytest.mark.usefixtures('postgres_db')
@pytest.mark.usefixtures('in_real_db')
@pytest.mark.usefixtures('restart_api')
@pytest.mark.usefixtures('restart_redis_pubsub')
def test_add_batch_and_allocate():
        #  start with to batches and an order allocated to one of them
        orderid, sku = random_orderid(), random_sku()

        earlier_batch, later_batch = random_batchref('newer'), random_batchref('old')

        api_client.post_to_add_batch(earlier_batch, sku, qty=10, eta='2011-01-02')

        api_client.post_to_add_batch(later_batch, sku, qty=10, eta='2011-01-03')

        response = api_client.post_to_allocate(orderid, sku, 10)
        print('old_batch: ' + later_batch)
        print('newer_batch: ' + earlier_batch)
        assert response.json()['batchref'] == earlier_batch

        r = api_client.post_list_batches(earlier_batch)
        print(r.text)


def test_publish_redis():
    subscription = redis_client.subscribe_to('line_allocated')

    #  change quantity on allocated batch so it's less than our order
    # redis_client.publish_message('line_allocated', {
    #     'batchref': earlier_batch, 'qty': 5
    # })

    redis_client.publish_message('line_allocated', "teste")


@pytest.mark.usefixtures('postgres_db')
# @pytest.mark.usefixtures('in_real_db')
# @pytest.mark.usefixtures('restart_api')
# @pytest.mark.usefixtures('restart_redis_pubsub')
def test_change_batch_quantity_leading_to_reallocation():
    #  start with to batches and an order allocated to one of them
    orderid, sku = random_orderid(), random_sku()

    earlier_batch, later_batch = random_batchref('newer'), random_batchref('old')

    api_client.post_to_add_batch(earlier_batch, sku, qty=10, eta='2011-01-02')

    api_client.post_to_add_batch(later_batch, sku, qty=10, eta='2011-01-03')

    response = api_client.post_to_allocate(orderid, sku, 10)
    assert response.json()['batchref'] == earlier_batch
    subscription = redis_client.subscribe_to('line_allocated')

    print(earlier_batch)
    #  change quantity on allocated batch so it's less than our order
    redis_client.publish_message('line_allocated', {
         'batchref': earlier_batch, 'qty': 5
    })

    #redis_client.publish_message('line_allocated', "teste")

    # wait until we see a message saying the order has been reallocated
    messages = []

    for attempt in Retrying(stop=stop_after_delay(3), reraise=True):
        with attempt:
            message = subscription.get_message(timeout=1)
            if message:
                messages.append(message)
                print(messages)
            #r = api_client.post_list_batches(earlier_batch)
            #print(r.text)
            data = json.loads(messages[-1]['data'])
            assert data['orderid'] == orderid
            assert data['batchref'] == later_batch
