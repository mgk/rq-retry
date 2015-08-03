build: clean
	python setup.py sdist bdist_wheel

clean:
	$(RM) -fr build dist *.egg-info .coverage htmlcov
	find . -name '*.pyc' | xargs rm -f

install:
	pip install -r requirements.txt
	pip install -r requirements-test.txt

install-dev: install
	pip install -r requirements-dev.txt

release: clean test
	bumpversion release
	python setup.py sdist bdist_wheel
	twine upload -r pypitest dist/*
	bumpversion --no-tag minor
	@echo
	@echo "so far so good..."
	@echo "wait for build green then:"
	@echo
	@echo "git push origin master --tags"
	@echo "twine upload dist/*"
	@echo
	@echo

test:
	pep8 rq_retry
	tox

coverage:
	coverage run --source=rq_retry -m py.test
	coverage run -a --source=rq_retry tests/run_no_rq_scheduler_test.py
	coverage html

.PHONY: build clean test coverage install install-dev release-test
