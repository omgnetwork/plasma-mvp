init:
	python setup.py install

.PHONY: help
help:
	@echo "root-chain" - starts the root chain
	@echo "child-chain"  starts the child chain
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - runs repos tests using pytest"

.PHONY: root-chain
root-chain:
	python deployment.py

.PHONY: child-chain
child-chain:
	python plasma/child_chain/server.py

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

.PHONY: lint
lint:
	flake8 plasma tests

.PHONY: test
test:
	python -m pytest

.PHONY: ganache
ganache:
	ganache-cli -m="plasma_mvp"
