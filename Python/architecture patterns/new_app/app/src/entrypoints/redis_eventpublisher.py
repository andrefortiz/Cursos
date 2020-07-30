import json
import logging

import redis
from dataclasses import asdict

import config
from domains import events

logging.basicConfig(filename='example.log', level=logging.INFO)
r = redis.Redis(**config.get_redis_host_and_port())


def publish(channel, event: events.Event):
    try:
        logging.info('publishing: channel=%s, event=s', channel, event)
        r.publish(channel, json.dumps(asdict(event)))
    except Exception as e:
        print(f'Out of stock for {e}')

