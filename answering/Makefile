PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
RUN := $(VENV)/bin/python

.PHONY: venv install test answer-sample answer-payload render-markdown render-json render-appendix run-all docker-build docker-run docker-up docker-down

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test:
	$(RUN) -m pytest

answer-sample:
	$(RUN) -m answering.app.cli answer sample

answer-payload:
	$(RUN) -m answering.app.cli answer --input payloads/sample_verified_payload.json

render-markdown:
	$(RUN) -m answering.app.cli render markdown --input payloads/sample_verified_payload.json

render-json:
	$(RUN) -m answering.app.cli render json --input payloads/sample_verified_payload.json

render-appendix:
	$(RUN) -m answering.app.cli render appendix --input payloads/sample_verified_payload.json

run-all:
	$(RUN) -m answering.app.cli run all

docker-build:
	docker compose build

docker-run:
	docker compose run --rm answering

docker-up:
	docker compose up --build --abort-on-container-exit --exit-code-from answering

docker-down:
	docker compose down -v
