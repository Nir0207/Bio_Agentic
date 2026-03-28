PYTHON ?= python

.PHONY: install test download load transform neo4j-up neo4j-init neo4j-load neo4j-validate run phase2 phase3 phase4 embeddings-generate embeddings-indexes embeddings-validate docker-neo4j docker-up docker-run

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

download:
	$(PYTHON) -m app.cli download all

load:
	$(PYTHON) -m app.cli load uniprot
	$(PYTHON) -m app.cli load string
	$(PYTHON) -m app.cli load reactome
	$(PYTHON) -m app.cli load pubmed

transform:
	$(PYTHON) -m app.cli transform gold

neo4j-init:
	$(PYTHON) -m app.cli neo4j init

neo4j-up:
	$(PYTHON) -m app.cli neo4j up

neo4j-load:
	$(PYTHON) -m app.cli neo4j load

neo4j-validate:
	$(PYTHON) -m app.cli neo4j validate

run:
	$(PYTHON) -m app.cli run all

phase2:
	$(PYTHON) -m app.cli run phase2

phase3:
	$(PYTHON) -m app.cli run phase3

phase4:
	$(PYTHON) -m app.cli run phase4

embeddings-generate:
	$(PYTHON) -m app.cli embeddings generate all

embeddings-indexes:
	$(PYTHON) -m app.cli embeddings init-indexes

embeddings-validate:
	$(PYTHON) -m app.cli embeddings validate

docker-neo4j:
	docker compose --profile neo4j up -d neo4j

docker-up:
	docker compose run --rm app neo4j up --no-start

docker-run:
	docker compose run --rm app run phase4
