import json
import redis

import config

r = redis.Redis(**config.get_redis_host_and_port())


def     subscribe_to(channel):
    r.set('test_result', 'It is working!')
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    confirmation = pubsub.get_message(timeout=3)
    assert confirmation['type'] == 'subscribe'
    return pubsub


def publish_message(channel, message):
    print(json.dumps(message))
    #r1 = redis.Redis(**config.get_redis_host_and_port(True))

    r.publish(channel, json.dumps(message))
    #r.publish(channel, message)
