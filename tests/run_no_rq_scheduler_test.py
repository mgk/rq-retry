#!/usr/bin/env python

import os
import pytest

if __name__ == '__main__':
    """Run this test by itself as it monkey patches __import__"""
    pytest.main(os.path.join('tests', 'no_rq_scheduler.py'))
