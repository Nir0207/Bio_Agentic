PYTHON ?= python3

.PHONY: install test run-sample run-query run-all inspect validate-tools docker-build docker-run

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

run-sample:
	$(PYTHON) -m orchestration.app.cli run sample

run-query:
	$(PYTHON) -m orchestration.app.cli run query --text "prioritize EGFR evidence"

run-all:
	$(PYTHON) -m orchestration.app.cli run all

inspect:
	$(PYTHON) -m orchestration.app.cli inspect-state --text "prioritize EGFR evidence"

validate-tools:
	$(PYTHON) -m orchestration.app.cli validate-tools

docker-build:
	docker compose build orchestration

docker-run:
	docker compose run --rm orchestration
