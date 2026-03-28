PYTHON ?= python

.PHONY: install test projection-create projection-list projection-inspect projection-drop estimate run-fastrp run-leiden run-knn run-all validate docker-build docker-run

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

projection-create:
	$(PYTHON) -m gds.app.cli projection create

projection-list:
	$(PYTHON) -m gds.app.cli projection list

projection-inspect:
	$(PYTHON) -m gds.app.cli projection inspect

projection-drop:
	$(PYTHON) -m gds.app.cli projection drop

estimate:
	$(PYTHON) -m gds.app.cli estimate all

run-fastrp:
	$(PYTHON) -m gds.app.cli run fastrp

run-leiden:
	$(PYTHON) -m gds.app.cli run leiden

run-knn:
	$(PYTHON) -m gds.app.cli run knn

run-all:
	$(PYTHON) -m gds.app.cli run all

validate:
	$(PYTHON) -m gds.app.cli validate

docker-build:
	docker compose build gds

docker-run:
	docker compose run --rm gds
