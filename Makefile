build:
	python setup.py sdist

clean:
	$(RM) -fr build dist *.egg-info .coverage htmlcov
	find . -name '*.pyc' | xargs rm -f

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pep8 rq_retry
	py.test
	python tests/run_no_rq_scheduler_test.py

coverage:
	coverage run --source=rq_retry setup.py test
	coverage run -a --source=rq_retry tests/run_no_rq_scheduler_test.py
	coverage html

.PHONY: build clean test coverage
