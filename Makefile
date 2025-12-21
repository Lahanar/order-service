.PHONY: help venv install test test-bottomup test-topdown test-sandwich coverage clean

help:
	@echo "Available commands:"
	@echo "  make venv          - create virtual environment"
	@echo "  make install       - install dependencies"
	@echo "  make test          - run pytest"
	@echo "  make test-bottomup - run bottom-up tests only"
	@echo "  make test-topdown  - run top-down tests only"
	@echo "  make test-sandwich - run sandwich tests only"
	@echo "  make coverage      - run tests with coverage report"
	@echo "  make clean         - remove virtual environment and caches"

venv:
	python3 -m venv venv
	@echo "Virtual environment created."

install:
	./venv/bin/pip install -r requirements.txt

test:
	./venv/bin/pytest -q

test-bottomup:
	./venv/bin/pytest -m bottomup -v

test-topdown:
	./venv/bin/pytest -m topdown -v

test-sandwich:
	./venv/bin/pytest -m sandwich -v

coverage:
	./venv/bin/pytest --cov=. --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

clean:
	rm -rf venv
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete