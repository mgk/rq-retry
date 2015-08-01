[![Build Status](https://travis-ci.org/mgk/rq-retry.svg?branch=master)](https://travis-ci.org/mgk/rq-retry)
[![Coverage Status](https://coveralls.io/repos/mgk/rq-retry/badge.svg?branch=master&service=github)](https://coveralls.io/github/mgk/rq-retry?branch=master)
[![Downloads](https://img.shields.io/pypi/dm/rq-retry.svg)](https://pypi.python.org/pypi/rq-retry)

# RQ Retry

[RQ Retry](https://github.com/mgk/rq-retry) is a package that adds retry functionality to the [RQ](http://python-rq.org/) queueing system. It can retry failed jobs immediately or optionally schedule them to retry after a delay using [RQ Scheduler](https://github.com/ui/rq-scheduler).

## Installation

```console
pip install rq-retry
pip install rq-scheduler # optional

```

## Using

Run worker process:

```console
rqworker -w rq_retry.RetryWorker
```

If using RQ Scheduler run the scheduler daemon:

```console
rqscheduler
```

The `RetryWorker` performs work like a regular RQ `Worker`. In addition it periodically checks for jobs on the failed queue and requeues them to be run again. If a job fails too many times it is moved to the dead letter queue and will not be tried again.

## Options

[RQ Retry](https://github.com/mgk/rq-retry) can be configured with environment variables.

Name                | Default  | Description
------------------- | -------- | -----------
RQ_RETRY_MAINT_INTERVAL      | 30       | How often, at most, to check for failed jobs. The cehck is not guaranteed to happen every `RQ_RETRY_MAINT_INTERVAL` seconds. See [Maintenance Tasks](#maintenance-tasks).
RQ_RETRY_MAX_TRIES           | 3        | Maximum number of time a job may be attempted. This includes the first time the job was run. So a value of 3 will try the job 2 times. A value of 1 or less disables retry. Zero has no special meaning.
RQ_RETRY_RETRY_DELAYS        | 5        | How long to delay each job retry in seconds. This can be a single float value or a comma separated list of floats. A simple  [exponential backoff](https://en.wikipedia.org/wiki/Exponential_backoff) can be achieved by using a value like `3,10,60`. This causes the first retry of each job to be delayed 3 seconds, the second retry 10 seconds, and the third and subsequent retries to be delayed 60 seconds. To disable, set to any non numeric value like `disabled`. When delays are disabled jobs are requeued immediately without using [RQ Scheduler](https://github.com/ui/rq-scheduler).
RQ_RETRY_DEAD_LETTER_QUEUE   | dead_letter_queue | name of dead letter queue


### Maintenance Tasks
`rqworker` is a command line wraper around an RQ `Worker`. It configures a Worker instance and then calls its `work()` method which loops indefinitely looking for jobs and running them. Workers also perform maintenance tasks periodically in their work loop. In the case of `RetryWorker` maintenance tasks include retrying failed jobs.

This means that `RetryWorker` failed job handling is only performed when the `RetryWorker` wakes up to handle a "regular" job from a queue. For this reason it is suggested that `RetryWorker` be used as a drop in replacement for `Worker`. In an active system this will ensure that failed jobs are retried promptly.

## Developing

Pull requests welcome.

Getting started:

```console
make install test
```

## License

See [LICENSE](LICENSE)
