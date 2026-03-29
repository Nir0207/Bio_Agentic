PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
RUN := $(VENV)/bin/python

.PHONY: venv install test verify-sample verify-payload inspect-claims inspect-verdict run-all docker-build docker-run docker-up docker-down

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test:
	$(RUN) -m pytest

verify-sample:
	$(RUN) -m verification.app.cli verify sample

verify-payload:
	$(RUN) -m verification.app.cli verify payload --input payloads/sample_orchestration_payload.json

inspect-claims:
	$(RUN) -m verification.app.cli inspect claims --input payloads/sample_orchestration_payload.json

inspect-verdict:
	$(RUN) -m verification.app.cli inspect verdict --input payloads/sample_orchestration_payload.json

run-all:
	$(RUN) -m verification.app.cli run all

docker-build:
	docker compose build

docker-run:
	docker compose run --rm verification

docker-up:
	docker compose up --build --abort-on-container-exit --exit-code-from verification

docker-down:
	docker compose down -v
