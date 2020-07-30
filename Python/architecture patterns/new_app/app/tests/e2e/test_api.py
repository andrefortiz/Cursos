import pytest
import requests

import config
from new_app.app.tests.random_def import random_sku, random_batchref, random_orderid


def post_to_add_batch(ref, sku, qty, eta):
    url = config.get_api_url()
    r = requests.post(f'{url}/add_batch', json={
        'ref': ref, 'sku': sku, 'qty': qty, 'eta': eta,
    })
    assert r.status_code == 201


@pytest.mark.usefixtures('in_real_db')
def test_list_batches():
    url = config.get_api_url()
    r = requests.get(f'{url}/batches')
    print(r)
    print(r.text)
    assert r.status_code == 200


@pytest.mark.usefixtures('postgres_db')
@pytest.mark.usefixtures('restart_api')
def test_happy_path_returns_202_and_batch_is_allocated():
    orderid = random_orderid()
    sku, othersku = random_sku(), random_sku('other')
    early_batch = random_batchref(1)
    later_order = random_orderid(1)
    other_order = random_orderid(1)

    post_to_add_batch(later_order, sku, 100, '2011-01-02')
    post_to_add_batch(early_batch, sku, 100, '2011-01-01')
    post_to_add_batch(other_order, othersku, 100, None)

    data = {'orderid': orderid, 'sku': sku, 'qty': 3}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    assert r.status_code == 202

    print(orderid)
    r = requests.get(f'{url}/allocations/{orderid}')
    assert r.ok
    assert r.json() == [
        {'sku': sku, 'batchref': early_batch}
    ]


@pytest.mark.usefixtures('restart_api')
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku = random_sku()
    order_id = random_orderid(1)

    data = {'orderid': order_id, 'sku': unknown_sku, 'qty': 20}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    assert r.status_code == 400
    assert r.json()['message'] == f'Invalid sku {unknown_sku}'

    r = requests.get(f'{url}/allocations/{order_id}')
    assert r.status_code == 404


@pytest.mark.usefixtures('in_memory_db')
@pytest.mark.usefixtures('restart_api')
def test_happy_path_returns_201_and_allocated_batch():
    sku, othersku = random_sku(), random_sku('other')
    early_batch = random_batchref(1)
    later_order = random_orderid(1)
    other_order = random_orderid(1)

    post_to_add_batch(later_order, sku, 100, '2011-01-02')
    post_to_add_batch(early_batch, sku, 100, '2011-01-01')
    post_to_add_batch(other_order, othersku, 100, None)

    data = {'orderid': random_orderid(), 'sku': sku, 'qty': 3}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    assert r.status_code == 201
    assert r.json()['batchref'] == early_batch


@pytest.mark.usefixtures('restart_api')
def test_400_message_for_out_of_stock():
    sku = random_sku()
    small_batch = random_batchref(1)
    large_order = random_orderid(1)

    post_to_add_batch(small_batch, sku, 100, '2011-01-02')

    data = {'orderid': large_order, 'sku': sku, 'qty': 120}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    assert r.status_code == 400
    assert r.json()['message'] == f'Out of stock for sku {sku}'


