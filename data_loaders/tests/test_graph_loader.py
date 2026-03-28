from __future__ import annotations

from pathlib import Path

import polars as pl

from graph.loader import Neo4jGraphLoader

from .conftest import make_settings


class FakeResult:
    def consume(self):
        return None


class FakeTx:
    def __init__(self, calls: list[dict]) -> None:
        self.calls = calls

    def run(self, query: str, parameters: dict):
        self.calls.append({"query": query, "parameters": parameters})
        return FakeResult()


class FakeSession:
    def __init__(self, calls: list[dict]) -> None:
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def execute_write(self, work):
        return work(FakeTx(self.calls))


class FakeDriver:
    def __init__(self, calls: list[dict]) -> None:
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def session(self, database: str):
        return FakeSession(self.calls)


def _write_protein_nodes(path: Path, count: int) -> None:
    rows = [
        {
            "id": f"protein:P{i:05d}",
            "uniprot_id": f"P{i:05d}",
            "name": f"Protein {i}",
            "organism": "Homo sapiens",
            "source": "UniProt",
            "reviewed": True,
        }
        for i in range(count)
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_parquet(path)


def test_loader_batches_by_configured_size(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, neo4j_batch_size=2)
    _write_protein_nodes(settings.gold_dir / "nodes_protein.parquet", count=5)

    calls: list[dict] = []
    loader = Neo4jGraphLoader(settings)
    loader._driver = lambda: FakeDriver(calls)  # type: ignore[method-assign]

    loader.load_all()

    # 5 rows with batch size 2 => 3 write batches.
    assert len(calls) == 3
    assert len(calls[0]["parameters"]["rows"]) == 2
    assert len(calls[1]["parameters"]["rows"]) == 2
    assert len(calls[2]["parameters"]["rows"]) == 1


def test_loader_dry_run_skips_neo4j_calls(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, neo4j_batch_size=2)
    _write_protein_nodes(settings.gold_dir / "nodes_protein.parquet", count=4)

    loader = Neo4jGraphLoader(settings)

    def _boom():
        raise AssertionError("Driver should not be created during dry-run")

    loader._driver = _boom  # type: ignore[method-assign]

    loader.load_all(dry_run=True)
    loader.init_constraints(dry_run=True)
