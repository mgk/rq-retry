import pytest

try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import patch, Mock

import os
import logging
from datetime import timedelta
from rq import Worker, Queue, get_failed_queue
from rq_retry import RetryWorker

from . import *


def success_fun():
    pass


def error_fun(*args, **kwargs):
    raise RuntimeError('I am an error')


def test_does_regular_work_like_any_good_worker():
    q = Queue()
    w = RetryWorker([q])
    q.enqueue(success_fun)
    w.work(burst=True)
    assert q.count == 0
    assert get_failed_queue().count == 0


def test_maint_interval():
    q = Queue()
    rw = RetryWorker([q], retry_config=dict(
        max_tries=2, maint_interval=100, delays=[]))
    w = Worker([q])
    job = q.enqueue(error_fun)
    w.work(burst=True)

    for _ in range(1, 20):
        rw.work(burst=True)

    job.refresh()
    assert q.count == 0
    assert get_failed_queue().count == 1
    assert Queue('dead_letter_queue').count == 0
    assert job.meta['tries'] == 2


def test_retry_worker_as_only_worker():
    q = Queue()
    rw = RetryWorker([q], retry_config=dict(
        max_tries=4, maint_interval=0, delays=[]))
    job = q.enqueue(error_fun)

    for _ in range(1, 20):
        rw.work(burst=True)

    job.refresh()
    assert q.count == 0
    assert get_failed_queue().count == 0
    assert Queue('dead_letter_queue').count == 1
    assert job.meta['tries'] == 4


def test_failed_job_max_tries_1__move_to_dlq():
    q = Queue()
    failed_q = get_failed_queue()
    dlq = Queue('dead_letter_queue')

    # we could test with one worker here, but we don't want
    # the test to depend on when the Worker performs maint.
    # tasks (before or after processing jobs)
    w = Worker([q])
    rw = RetryWorker([q], retry_config=dict(
        max_tries=1, delays=[]))

    # run job that will fail
    job = q.enqueue(error_fun)
    w.work(burst=True)
    assert q.count == 0
    assert get_failed_queue().count == 1

    # run retry worker
    rw.work(burst=True)
    job.refresh()

    assert q.count == 0
    assert failed_q.count == 0
    assert dlq.count == 1
    assert job.meta['tries'] == 1


def test_failed_job_max_tries_2__retry_once_then_move_to_dlq():
    q = Queue()
    q2 = Queue('not_used')
    failed_q = get_failed_queue()
    dlq = Queue('dead_letter_queue')

    w = Worker([q])

    # Here the RetryWorker not listening on an active queue: it will not
    # run any jobs, just look to requeue failed jobs.
    rw = RetryWorker([q2], retry_config=dict(
        max_tries=2, maint_interval=0, delays=[]))

    # run job that will fail
    job = q.enqueue(error_fun)
    w.work(burst=True)
    assert q.count == 0
    assert get_failed_queue().count == 1

    # run retry worker
    rw.work(burst=True)

    # job should be requeued
    assert q.count == 1
    assert failed_q.count == 0
    assert dlq.count == 0
    job.refresh()
    assert job.meta['tries'] == 2

    # regular worker runs the job again
    w.work(burst=True)

    # job fails again
    assert q.count == 0
    assert failed_q.count == 1
    assert dlq.count == 0
    job.refresh()
    assert job.meta['tries'] == 2

    # run retry worker
    rw.work(burst=True)

    # job should be in dlq
    assert q.count == 0
    assert failed_q.count == 0
    assert dlq.count == 1
    job.refresh()
    assert job.meta['tries'] == 2


@patch('rq_scheduler.Scheduler', autospec=True)
def test_uses_rq_scheduler_with_args_and_kwargs(MockScheduler):
    q = Queue()
    w = Worker([q])

    # run job with args and kwargs that will fail
    job = q.enqueue(error_fun, 1, 2, a=3, b=4)
    w.work(burst=True)

    # run retry worker configured to use rq_scheduler
    q2 = Queue('unused')
    rw = RetryWorker([q2], retry_config=dict(delays=[42]))
    rw.work(burst=True)

    MockScheduler.return_value.enqueue_in.assert_called_once_with(
        timedelta(seconds=42), error_fun, 1, 2, a=3, b=4)


@patch('rq_scheduler.Scheduler', autospec=True)
def test_delays_ev(MockScheduler):
    q = Queue()
    w = Worker([q])
    job = q.enqueue(error_fun)
    w.work(burst=True)

    # run retry worker configured to use rq_scheduler
    q2 = Queue('unused')

    os.environ['RQ_RETRY_DELAYS'] = '1'
    rw = RetryWorker([q2])
    rw.work(burst=True)
    MockScheduler.return_value.enqueue_in.assert_called_once_with(
        timedelta(seconds=1), error_fun)
    del os.environ['RQ_RETRY_DELAYS']


def test_disable_scheduler_with_delays_ev():
    os.environ['RQ_RETRY_DELAYS'] = 'any non numeric here'
    rw = RetryWorker([Queue()])
    assert not rw.use_scheduler
    del os.environ['RQ_RETRY_DELAYS']


def test_max_tries_ev():
    os.environ['RQ_RETRY_MAX_TRIES'] = '7'
    rw = RetryWorker([Queue()])
    assert rw.max_tries == 7
    del os.environ['RQ_RETRY_MAX_TRIES']


@patch('rq_scheduler.Scheduler', autospec=True)
def test_too_few_delays(MockScheduler):
    q = Queue()
    w = Worker([q])
    job = q.enqueue(error_fun)
    q2 = Queue('unused')

    rw = RetryWorker([q2], retry_config=dict(
        maint_interval=0, max_tries=20, delays=[5]))

    w.work(burst=True)
    job.refresh()
    job.meta['tries'] = 10
    job.save()
    rw.work(burst=True)

    MockScheduler.return_value.enqueue_in.assert_called_once_with(
        timedelta(seconds=5), error_fun)


def test_max_tries_large():
    q = Queue()
    q2 = Queue('unused')
    w = Worker([q])
    rw = RetryWorker([q2], retry_config=dict(
        max_tries=2**80, maint_interval=0, delays=[]))
    job = q.enqueue(error_fun)

    for _ in range(1, 10):
        w.work(burst=True)
        rw.work(burst=True)

    job.refresh()
    assert q.count == 1
    assert get_failed_queue().count == 0
    assert Queue('dead_letter_queue').count == 0
    assert job.meta['tries'] == 10
