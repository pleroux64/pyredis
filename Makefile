.PHONY: install run test lint clean clean-data help

PYTHON := python3

help:
	@echo "make install     install pyredis (editable) + dev dependencies (pytest, ruff)"
	@echo "make run         start the pyredis server on 127.0.0.1:65432"
	@echo "make test        run the test suite (verbose)"
	@echo "make lint        run ruff over the project"
	@echo "make clean       remove __pycache__ / .pytest_cache"
	@echo "make clean-data  remove wal.log / snapshot.json (runtime state)"

install:
	$(PYTHON) -m pip install -e . -r requirements-dev.txt

run:
	$(PYTHON) -m pyredis

test:
	$(PYTHON) -m pytest -v

lint:
	$(PYTHON) -m ruff check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache

clean-data:
	rm -f wal.log snapshot.json
