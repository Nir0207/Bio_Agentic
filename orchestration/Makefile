PYTHON ?= python3

.PHONY: install test run-sample run-query run-all inspect validate-tools bootstrap-sample-db docker-build docker-run docker-up docker-down

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

bootstrap-sample-db:
	$(PYTHON) -m orchestration.app.cli bootstrap sample-db

docker-build:
	docker compose build

docker-run:
	docker compose run --rm orchestration

docker-up:
	docker compose up --build --abort-on-container-exit --exit-code-from orchestration

docker-down:
	docker compose down -v
