#!/usr/bin/env python

import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

here = os.path.abspath(os.path.dirname(__file__))


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name='rq-retry',
    version='0.0.2',
    description='RQ retry worker and dead letter queue',
    long_description=__doc__,
    url='https://github.com/mgk/rq-retry',
    author='Michael Keirnan',
    author_email='michael@keirnan.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['rq'],
    tests_require=['pytest', 'redis>=2.7.0', 'rq-scheduler>=0.5.1'],
    cmdclass={'test': PyTest},
    extras_require={
        'scheduled_retry': ['rq_scheduler>=0.5.1'],
    },
    zip_safe=True,
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
