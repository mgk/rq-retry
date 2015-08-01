import os
from datetime import datetime, timedelta
from rq.queue import Queue
from rq.worker import Worker
from .queue import DeadLetterQueue

try:
    import rq_scheduler
except ImportError:
    rq_scheduler = None


class RetryWorker(Worker):
    """Worker class that periodically retries jobs on the FailedQueue.

    All Workers check for maintenance tasks after running each job. The
    RetryWorker retries jobs on the failed queue as part of its maintenance
    tasks. The RetryWorker also has a configurable interval for how often
    maintenance is performed.

    All parameters supported by Worker are supported by RetryWorker. In
    addition the parameters below, which must be passed as keyword
    arguments are accepted.

    Each parameter below can also be set by an environment variable
    with its name uppercased. Examples below.

    Settings
    --------
    maint_interval : timedelta or float or str
        How often to perform maintenance tasks, i.e., to check for failed
        jobs, as a `timedelta` or as a `float` or `str` value in seconds.
        *Environment variable*: `RQ_RETRY_MAINT_INTERVAL`
        *Default*: time

    max_tries : int or str
        Maximum number of times a job will be attempted before being moved
        to the dead letter queue. A value of 2 means retry a job one time if
        it fails. A value of 1 or less means do not retry the job. To retry
        a job indefinitely use a large value.
        *Environment variable*: `RQ_RETRY_MAX_TRIES`
        *Default*: 3

    delays : list(float) or str
        Delays to use before each retry attempt, in seconds.
        The first retry of a job uses the first delay in the list,
        the second retry uses the second delay, etc. If there are not
        enough delays in the list the last value is repeated. So to set a
        delay of 5 seconds for all retries use `[5]`. To set with environment
        variable use a comma separated list of numbers, no spaces:
        *Environment variable*: `RQ_RETRY_DELAYS`
        *Default*: [5]

    dead_letter_queue : str
        Name of dead letter queue. The default of `dead_letter_queue`
        does not normally need to be changed unless you have multiple
        dead letter queues.
        *Environment variable*: `RQ_RETRY_DEAD_LETTER_QUEUE`
        *Default*: 'dead_letter_queue'
    """
    def __init__(self, *args, **kwargs):
        default_config = dict(
            maint_interval=timedelta(seconds=30),
            max_tries=3,
            delays=[5],
            dead_letter_queue='dead_letter_queue')

        retry_config = kwargs.pop('retry_config', {})

        self.apply_config(retry_config, default_config)
        if not isinstance(self.maint_interval, timedelta):
            self.maint_interval = timedelta(seconds=float(self.maint_interval))

        if isinstance(self.max_tries, str):
            self.max_tries = int(self.max_tries)

        if isinstance(self.delays, str):
            try:
                self.delays = list(map(float, self.delays.split(',')))
            except ValueError:
                self.delays = []

        super(RetryWorker, self).__init__(*args, **kwargs)
        self._dead_letter_queue = DeadLetterQueue(self.dead_letter_queue,
                                                  connection=self.connection)

    def apply_config(self, config, defaults):
        for name, default_value in defaults.items():
            value = config.get(name)
            if value is None:
                value = os.environ.get('RQ_RETRY_{}'.format(name.upper()))
            if value is None:
                value = default_value
            setattr(self, name, value)

    def register_birth(self):
        for p in ['maint_interval',
                  'max_tries',
                  'delays',
                  'dead_letter_queue']:
            self.log.info('{} = {}'.format(p, getattr(self, p)))
        self.log.info('Use RQ Scheduler? {}'.format(self.use_scheduler))
        super(RetryWorker, self).register_birth()

    @property
    def use_scheduler(self):
        return rq_scheduler is not None and len(self.delays) > 0

    @property
    def should_run_maintenance_tasks(self):
        return (
            self.last_cleaned_at is None or
            (datetime.utcnow() - self.last_cleaned_at) > self.maint_interval
        )

    def clean_registries(self):
        super(RetryWorker, self).clean_registries()
        self.retry_failed_jobs()

    def retry_failed_jobs(self):
        self.log.info('Checking for failed jobs')
        for job in self.failed_queue.jobs:
            self.retry_failed_job(job)

    def retry_failed_job(self, job):
        job.meta['tries'] = job.meta.get('tries', 1)
        if job.meta['tries'] < self.max_tries:
            self.log.info('Retrying {job}, tries={tries}'.format(
                          job=job,
                          tries=job.meta['tries'] - 1))
            self.requeue_job(job)

        else:
            self.log.warning('Moving {job} to {name!r} queue'.format(
                             job=job,
                             name=self._dead_letter_queue.name))
            self._dead_letter_queue.quarantine(job, self.failed_queue)

    def requeue_job(self, job):
        if self.use_scheduler:
            tries = job.meta['tries']
            try:
                delay = self.delays[tries - 1]
            except IndexError:
                delay = self.delays[-1]

            scheduler = rq_scheduler.Scheduler(connection=self.connection,
                                               queue_name=job.origin)

            self.failed_queue.remove(job)
            job = scheduler.enqueue_in(timedelta(seconds=delay),
                                       job.func,
                                       *job.args,
                                       **job.kwargs)
            job.meta['tries'] = tries + 1
            job.save()
            self.log.info('scheduled to run in {} seconds'.format(delay))
        else:
            job.meta['tries'] += 1
            job.save()
            self.failed_queue.requeue(job.id)
            self.log.info('requeued')
