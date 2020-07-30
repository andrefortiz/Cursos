import requests

import config


def post_list_batches(ref, local: bool = False):
    url = config.get_api_url(local)
    r = requests.post(f'{url}/batches', json={
        'ref': ref,
    })
    print(r)
    assert r.status_code == 200
    return r


def post_to_add_batch(ref, sku, qty, eta, local: bool = False):
    url = config.get_api_url(local)
    r = requests.post(f'{url}/add_batch', json={
        'ref': ref, 'sku': sku, 'qty': qty, 'eta': eta,
    })
    assert r.status_code == 201


def post_to_allocate(orderid, sku, qty, expect_success=True, local: bool = False):
    url = config.get_api_url(local)
    r = requests.post(f'{url}/allocate', json={
        'orderid': orderid, 'sku': sku, 'qty': qty,
    })
    if expect_success:
        assert r.status_code == 202
    return r
