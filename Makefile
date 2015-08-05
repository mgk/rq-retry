build: clean
	python setup.py sdist bdist_wheel

clean:
	$(RM) -fr build dist *.egg-info .coverage htmlcov

very-clean: clean
	find . -name '*.pyc' | xargs rm -f

install:
	pip install -r requirements.txt
	pip install -r requirements-test.txt

install-dev: install
	pip install -r requirements-dev.txt

release: clean test
	PYTHONPATH=. bumpversion --post-hook bump.hook release
	python setup.py sdist bdist_wheel
	twine upload -r pypitest dist/*
	git push origin master --tags
	PYTHONPATH=. bumpversion --no-tag --post-hook bump.hook minor
	@echo
	@echo "so far so good..."
	@echo "wait for Travis green light, then:"
	@echo
	@echo "twine upload dist/*"

test:
	pep8 rq_retry
	tox

coverage:
	coverage run --source=rq_retry -m py.test
	coverage run -a --source=rq_retry tests/run_no_rq_scheduler_test.py
	coverage html

.PHONY: build clean test coverage install install-dev release-test
