init:
	python setup.py install

.PHONY: help
help:
	@echo "root-chain  - deploys the root chain contract"
	@echo "child-chain - starts the child chain"
	@echo "clean       - remove build artifacts"
	@echo "lint        - check style with flake8"
	@echo "test        - run tests with pytest"

.PHONY: root-chain
root-chain:
	python deployment.py

.PHONY: child-chain
child-chain:
	PYTHONPATH=. python plasma/child_chain/server.py

.PHONY: clean
clean: clean-build clean-pyc

.PHONY: clean-build
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '*pycache__' -exec rm -rf {} +
	find . -name '.pytest_cache' -exec rm -rf {} +

.PHONY: lint
lint:
	flake8 plasma plasma_core testlang tests

.PHONY: test
test:
	python -m pytest
	find . -name '.pytest_cache' -exec rm -rf {} +

.PHONY: dev
dev:
	pip install pytest pylint flake8

.PHONY: ganache
ganache:
	ganache-cli -m="plasma_mvp"
