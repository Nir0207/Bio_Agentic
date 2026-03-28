PYTHON ?= python3

.PHONY: install test projection-create projection-list projection-inspect projection-drop estimate run-fastrp run-leiden run-knn run-all validate docker-build docker-run

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

projection-create:
	$(PYTHON) -m graphML.app.cli projection create

projection-list:
	$(PYTHON) -m graphML.app.cli projection list

projection-inspect:
	$(PYTHON) -m graphML.app.cli projection inspect

projection-drop:
	$(PYTHON) -m graphML.app.cli projection drop

estimate:
	$(PYTHON) -m graphML.app.cli estimate all

run-fastrp:
	$(PYTHON) -m graphML.app.cli run fastrp

run-leiden:
	$(PYTHON) -m graphML.app.cli run leiden

run-knn:
	$(PYTHON) -m graphML.app.cli run knn

run-all:
	$(PYTHON) -m graphML.app.cli run all

validate:
	$(PYTHON) -m graphML.app.cli validate

docker-build:
	docker compose build graphml

docker-run:
	docker compose run --rm graphml
