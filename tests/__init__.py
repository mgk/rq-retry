import logging
import redis
from rq import push_connection, pop_connection


def find_empty_redis_database():
    """Tries to connect to a random Redis database (starting from 4), and
    will use/connect it when no keys are in there.
    """
    for dbnum in range(4, 17):
        testconn = redis.StrictRedis(db=dbnum)
        empty = len(testconn.keys('*')) == 0
        if empty:
            return testconn
    assert False, 'No empty Redis database found to run tests in.'


def setup_module(module):
    logging.disable(logging.ERROR)
    globals()['conn'] = find_empty_redis_database()
    push_connection(conn)


def teardown_module(module):
    logging.disable(logging.NOTSET)
    assert pop_connection() == conn


def setup_function(function):
    conn.flushdb()


def teardown_function(function):
    conn.flushdb()
