PYTHON ?= python3

.PHONY: install test dataset-build dataset-inspect train evaluate register predict predict-batch writeback run-all docker-build docker-run

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

dataset-build:
	$(PYTHON) -m modeling.app.cli dataset build

dataset-inspect:
	$(PYTHON) -m modeling.app.cli dataset inspect

train:
	$(PYTHON) -m modeling.app.cli train baseline

evaluate:
	$(PYTHON) -m modeling.app.cli evaluate latest

register:
	$(PYTHON) -m modeling.app.cli register latest

predict:
	$(PYTHON) -m modeling.app.cli predict --protein-id P00533

predict-batch:
	$(PYTHON) -m modeling.app.cli predict-batch

writeback:
	$(PYTHON) -m modeling.app.cli writeback scores

run-all:
	$(PYTHON) -m modeling.app.cli run all

docker-build:
	docker compose build modeling

docker-run:
	docker compose run --rm modeling
