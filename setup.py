"""
|Build Status| |Coverage Status| |Downloads|

RQ Retry
========

`RQ Retry`_ is a package that adds retry functionality to the `RQ`_
queueing system. It can retry failed jobs immediately or optionally
schedule them to retry after a delay using `RQ Scheduler`_.

Installation
============

.. code::

    pip install rq-retry
    pip install rq-scheduler # optional

Usage
=====

Run worker process:

.. code::

    rqworker -w rq_retry.RetryWorker
    rqscheduler # optional

`See Documentation for details`_

.. _See Documentation for details: https://github.com/mgk/rq-retry/blob/master/README.md
.. _RQ Retry: https://github.com/mgk/rq-retry/blob/master/README.md
.. _RQ: http://python-rq.org/
.. _RQ Scheduler: https://github.com/ui/rq-scheduler

.. |Build Status| image:: https://travis-ci.org/mgk/rq-retry.svg?branch=master
   :target: https://travis-ci.org/mgk/rq-retry
.. |Coverage Status| image:: https://coveralls.io/repos/mgk/rq-retry/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/mgk/rq-retry?branch=master
.. |Downloads| image:: https://img.shields.io/pypi/dm/rq-retry.svg
   :target: https://pypi.python.org/pypi/rq-retry
"""
import os
import sys

from setuptools import setup, find_packages

setup(
    name='rq-retry',
    version='0.2.0',
    description='RQ retry support',
    long_description=__doc__,
    url='https://github.com/mgk/rq-retry/blob/master/README.md',
    author='Michael Keirnan',
    author_email='michael@keirnan.com',
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    install_requires=['rq'],
    tests_require=['pytest', 'redis>=2.7.0', 'rq-scheduler>=0.5.1'],
    extras_require={
        'scheduled_retry': ['rq_scheduler>=0.5.1'],
    },
    zip_safe=False,
    platforms='any',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Monitoring',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ]
)
