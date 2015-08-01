#!/usr/bin/env python
"""
A bit of ugliness here to test the:

try:
    import foo
except:
    foo = None

pattern used by the unit under test.

This test needs to be run in a separate python invocation from other tests.
It monkey patches the __import__ to simulate rq_scheduler not being present.
"""
import pytest
from rq import Queue, Worker, get_failed_queue
from tests import *


def error_fun():
    raise RuntimeError()


def test_no_rq_scheduler_falls_back_to_immediate_retry():
    q = Queue()
    q2 = Queue('not_used')

    w = Worker([q])
    rw = get_retry_worker()([q2], retry_config=dict(
        max_tries=2, retry_delays=[1], maint_interval=0))

    # run job that will fail
    job = q.enqueue(error_fun)
    w.work(burst=True)
    assert q.count == 0
    assert get_failed_queue().count == 1

    # run retry worker
    rw.work(burst=True)

    # job should be requeued since rq_scheduler cannot be imported
    assert q.count == 1
    assert get_failed_queue().count == 0
    assert Queue('dead_letter_queue').count == 0
    job.refresh()
    assert job.meta['tries'] == 2


def get_retry_worker():
    try:
        import builtins
    except ImportError:
        import __builtin__ as builtins

    realimport = builtins.__import__

    def myimport(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'rq_scheduler':
            raise ImportError
        return realimport(name, globals, locals, fromlist, level)

    builtins.__import__ = myimport
    from rq_retry import RetryWorker
    builtins.__import__ = realimport

    return RetryWorker


if __name__ == '__main__':
    pytest.main(['--debug', 'tests/xtest_no_rq_scheduler.py'])
