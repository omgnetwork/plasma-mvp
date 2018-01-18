.PHONY: help
help:
	@echo "root-chain" - starts the root chain and
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - runs repos tests using pytest"

.PHONY: root-chain
root-chain:
	python deployment.py

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

.PHONY: lint
lint:
	flake8 plasma tests

.PHONY: test
test:
	python -m pytest
