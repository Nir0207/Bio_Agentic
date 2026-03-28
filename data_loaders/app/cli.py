from __future__ import annotations

import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

import typer
from neo4j import GraphDatabase

from app.config import get_settings
from app.logging import configure_logging

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from embeddings.config import EmbeddingConfig
from embeddings.generators import build_evidence_generator, build_publication_generator
from embeddings.registry import get_embedding_model
from embeddings.retrieval.vector_search import VectorSearchService
from embeddings.validation.embedding_checks import run_embedding_validation_checks
from embeddings.writers.neo4j_writer import Neo4jEmbeddingWriter
from graph.loader import Neo4jGraphLoader
from graph.validate import ValidationSummary, run_validations
from pipelines.download.pubmed_downloader import PubMedDownloader
from pipelines.download.reactome_downloader import ReactomeDownloader
from pipelines.download.string_downloader import StringDownloader
from pipelines.download.uniprot_downloader import UniProtDownloader
from pipelines.loaders.pubmed_loader import PubMedLoader
from pipelines.loaders.reactome_loader import ReactomeLoader
from pipelines.loaders.string_loader import StringLoader
from pipelines.loaders.uniprot_loader import UniProtLoader
from pipelines.transforms.graph_tables import build_graph_tables

app = typer.Typer(add_completion=False, help="Load filtered pharma graph data into local Neo4j.")
download_app = typer.Typer(add_completion=False)
load_app = typer.Typer(add_completion=False)
neo4j_app = typer.Typer(add_completion=False)
transform_app = typer.Typer(add_completion=False)
run_app = typer.Typer(add_completion=False)
embeddings_app = typer.Typer(add_completion=False)
embeddings_generate_app = typer.Typer(add_completion=False)

app.add_typer(download_app, name="download")
app.add_typer(load_app, name="load")
app.add_typer(neo4j_app, name="neo4j")
app.add_typer(transform_app, name="transform")
app.add_typer(run_app, name="run")
app.add_typer(embeddings_app, name="embeddings")
embeddings_app.add_typer(embeddings_generate_app, name="generate")


@download_app.command("all")
def download_all(force: bool = typer.Option(False, "--force")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    downloaders = [
        UniProtDownloader(settings),
        PubMedDownloader(settings),
        ReactomeDownloader(settings),
    ]
    with ThreadPoolExecutor(max_workers=len(downloaders)) as executor:
        futures = {executor.submit(downloader.download, force=force): downloader.__class__.__name__ for downloader in downloaders}
        failures: list[str] = []
        for future in as_completed(futures):
            name = futures[future]
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{name}: {exc}")
                typer.echo(f"{name} download failed: {exc}", err=True)
            else:
                typer.echo(f"{name} download complete")
        if failures:
            typer.echo("Some downloads failed; continuing with available sources.", err=True)


@download_app.command("string")
def download_string(force: bool = typer.Option(False, "--force")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    if not settings.string_download_enabled:
        typer.echo("STRING download is disabled; set STRING_DOWNLOAD_ENABLED=true to enable it.", err=True)
        raise typer.Exit(code=1)
    StringDownloader(settings).download(force=force)


@load_app.command("uniprot")
def load_uniprot(force: bool = typer.Option(False, "--force")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    UniProtLoader(settings).load(force=force)


@load_app.command("string")
def load_string(force: bool = typer.Option(False, "--force")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    StringLoader(settings).load(force=force)


@load_app.command("reactome")
def load_reactome(force: bool = typer.Option(False, "--force")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    ReactomeLoader(settings).load(force=force)


@load_app.command("pubmed")
def load_pubmed(force: bool = typer.Option(False, "--force")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    PubMedLoader(settings).load(force=force)


@transform_app.command("gold")
def transform_gold() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    build_graph_tables(settings)


@neo4j_app.command("init")
def neo4j_init(
    dry_run: bool = typer.Option(False, "--dry-run", help="Print actions without executing Cypher."),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    Neo4jGraphLoader(settings).init_constraints(dry_run=dry_run)


@neo4j_app.command("load")
def neo4j_load(
    dry_run: bool = typer.Option(False, "--dry-run", help="Print batch plan without writing to Neo4j."),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    Neo4jGraphLoader(settings).load_all(dry_run=dry_run)


@neo4j_app.command("validate")
def neo4j_validate() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    summary = run_validations(settings, raise_on_critical=False)
    _print_validation_summary(summary)
    if summary.has_critical_issues:
        raise typer.Exit(code=1)


@neo4j_app.command("up")
def neo4j_up(
    wait_seconds: int = typer.Option(120, "--wait-seconds", min=1),
    uri: str = typer.Option("bolt://localhost:7688", "--uri"),
    username: str = typer.Option("neo4j", "--username"),
    password: str = typer.Option("neo4j-password", "--password"),
    start: bool = typer.Option(True, "--start/--no-start"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    if start:
        try:
            subprocess.run(["docker", "compose", "--profile", "neo4j", "up", "-d", "neo4j"], check=True)
        except FileNotFoundError:
            typer.echo(
                "Docker CLI is not available in this runtime; skipping compose start and only waiting for Neo4j.",
                err=True,
            )
        except subprocess.CalledProcessError as exc:
            typer.echo(f"Failed to start Neo4j via docker compose: {exc}", err=True)
            raise typer.Exit(code=1)
    deadline = time.monotonic() + wait_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with GraphDatabase.driver(uri, auth=(username, password)) as driver:
                with driver.session(database=settings.neo4j_database) as session:
                    session.run("RETURN 1").consume()
            typer.echo(f"Neo4j is ready at {uri}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2)
    typer.echo(f"Timed out waiting for Neo4j at {uri}. Last error: {last_error}", err=True)
    raise typer.Exit(code=1)


@embeddings_generate_app.command("publication")
def embeddings_generate_publication(
    force: bool = typer.Option(False, "--force"),
    max_nodes: int | None = typer.Option(None, "--max-nodes"),
) -> None:
    _generate_embeddings(target="publication", force=force, max_nodes=max_nodes)


@embeddings_generate_app.command("evidence")
def embeddings_generate_evidence(
    force: bool = typer.Option(False, "--force"),
    max_nodes: int | None = typer.Option(None, "--max-nodes"),
) -> None:
    _generate_embeddings(target="evidence", force=force, max_nodes=max_nodes)


@embeddings_generate_app.command("all")
def embeddings_generate_all(
    force: bool = typer.Option(False, "--force"),
    max_nodes: int | None = typer.Option(None, "--max-nodes"),
) -> None:
    _generate_embeddings(target="all", force=force, max_nodes=max_nodes)


@embeddings_app.command("init-indexes")
def embeddings_init_indexes() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    config = EmbeddingConfig.from_settings(settings)
    embedder = get_embedding_model(config.model_name, config.device)
    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    ) as driver:
        service = VectorSearchService(driver=driver, database=settings.neo4j_database, config=config, embedder=embedder)
        dims = service.init_indexes()
    typer.echo("Vector indexes initialized")
    typer.echo(f"- Publication index: {config.publication_index_name} (dim={dims['Publication']})")
    typer.echo(f"- Evidence index: {config.evidence_index_name} (dim={dims['Evidence']})")


@embeddings_app.command("validate")
def embeddings_validate() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    config = EmbeddingConfig.from_settings(settings)
    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    ) as driver:
        report = run_embedding_validation_checks(driver=driver, database=settings.neo4j_database, config=config)

    typer.echo("Embedding Validation")
    typer.echo("--------------------")
    for key, value in report.checks.items():
        typer.echo(f"{key}: {value}")
    if report.warnings:
        typer.echo("warnings:")
        for warning in report.warnings:
            typer.echo(f"  - {warning}")
    if report.critical_issues:
        typer.echo("critical_issues:")
        for issue in report.critical_issues:
            typer.echo(f"  - {issue}")
        raise typer.Exit(code=1)


@embeddings_app.command("search-publication")
def embeddings_search_publication(
    query: str = typer.Option(..., "--query"),
    top_k: int = typer.Option(5, "--top-k", min=1),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    config = EmbeddingConfig.from_settings(settings)
    embedder = get_embedding_model(config.model_name, config.device)
    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    ) as driver:
        service = VectorSearchService(driver=driver, database=settings.neo4j_database, config=config, embedder=embedder)
        results = service.search_publication(query=query, top_k=top_k)
    _print_search_results(results)


@embeddings_app.command("search-evidence")
def embeddings_search_evidence(
    query: str = typer.Option(..., "--query"),
    top_k: int = typer.Option(5, "--top-k", min=1),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    config = EmbeddingConfig.from_settings(settings)
    embedder = get_embedding_model(config.model_name, config.device)
    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    ) as driver:
        service = VectorSearchService(driver=driver, database=settings.neo4j_database, config=config, embedder=embedder)
        results = service.search_evidence(query=query, top_k=top_k)
    _print_search_results(results)


@run_app.command("all")
def run_all(force: bool = typer.Option(False, "--force")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    download_all(force=force)
    load_uniprot(force=force)
    load_string(force=force)
    load_reactome(force=force)
    load_pubmed(force=force)
    transform_gold()
    loader = Neo4jGraphLoader(settings)
    loader.init_constraints()
    loader.load_all()
    summary = run_validations(settings, raise_on_critical=False)
    _print_validation_summary(summary)
    if summary.has_critical_issues:
        raise typer.Exit(code=1)


@run_app.command("phase2")
def run_phase2() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    transform_gold()


@run_app.command("phase3")
def run_phase3(
    dry_run: bool = typer.Option(False, "--dry-run", help="Run init/load in dry-run mode."),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    loader = Neo4jGraphLoader(settings)
    loader.init_constraints(dry_run=dry_run)
    loader.load_all(dry_run=dry_run)
    if dry_run:
        typer.echo("phase3 dry-run complete; validation skipped because Neo4j writes were not executed.")
        return
    summary = run_validations(settings, raise_on_critical=False)
    _print_validation_summary(summary)
    if summary.has_critical_issues:
        raise typer.Exit(code=1)


@run_app.command("phase4")
def run_phase4(
    force: bool = typer.Option(False, "--force"),
    sample_query: str = typer.Option("protein interaction evidence", "--sample-query"),
    top_k: int = typer.Option(3, "--top-k", min=1),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    _generate_embeddings(target="all", force=force, max_nodes=None)
    embeddings_init_indexes()

    config = EmbeddingConfig.from_settings(settings)
    embedder = get_embedding_model(config.model_name, config.device)
    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    ) as driver:
        report = run_embedding_validation_checks(driver=driver, database=settings.neo4j_database, config=config)
        typer.echo("Embedding Validation")
        typer.echo("--------------------")
        for key, value in report.checks.items():
            typer.echo(f"{key}: {value}")
        if report.warnings:
            typer.echo("warnings:")
            for warning in report.warnings:
                typer.echo(f"  - {warning}")
        if report.critical_issues:
            typer.echo("critical_issues:")
            for issue in report.critical_issues:
                typer.echo(f"  - {issue}")
            raise typer.Exit(code=1)

        service = VectorSearchService(driver=driver, database=settings.neo4j_database, config=config, embedder=embedder)
        sample_results = service.merged_search(query=sample_query, top_k_each=top_k)
        typer.echo(f"Sample semantic search for query: {sample_query}")
        for index, row in enumerate(sample_results, start=1):
            typer.echo(
                f"{index}. [{row['label']}] id={row['node_id']} score={row['score']:.4f} "
                f"snippet={row['snippet']}"
            )


def _print_validation_summary(summary: ValidationSummary) -> None:
    typer.echo("Validation Summary")
    typer.echo("------------------")
    for query_name, rows in summary.query_results.items():
        typer.echo(f"{query_name}: {len(rows)} row(s)")
    typer.echo("relationship_endpoint_integrity:")
    for report in summary.endpoint_integrity:
        typer.echo(
            "  "
            f"{report['relationship']}: "
            f"missing_source_rows={report['missing_source_rows']}, "
            f"missing_target_rows={report['missing_target_rows']}, "
            f"missing_either_rows={report['missing_either_rows']}"
        )
    if summary.warnings:
        typer.echo("warnings:")
        for warning in summary.warnings:
            typer.echo(f"  - {warning}")
    if summary.critical_issues:
        typer.echo("critical_issues:")
        for issue in summary.critical_issues:
            typer.echo(f"  - {issue}")


def _generate_embeddings(target: str, *, force: bool, max_nodes: int | None) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    config = EmbeddingConfig.from_settings(settings)
    embedder = get_embedding_model(config.model_name, config.device)
    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    ) as driver:
        writer = Neo4jEmbeddingWriter(
            driver=driver,
            database=settings.neo4j_database,
            write_batch_size=config.write_batch_size,
        )
        targets = ["publication", "evidence"] if target == "all" else [target]
        for item in targets:
            if item == "publication":
                generator = build_publication_generator(
                    driver=driver,
                    database=settings.neo4j_database,
                    config=config,
                    embedder=embedder,
                )
                label = "Publication"
            elif item == "evidence":
                generator = build_evidence_generator(
                    driver=driver,
                    database=settings.neo4j_database,
                    config=config,
                    embedder=embedder,
                )
                label = "Evidence"
            else:
                raise ValueError(f"Unsupported embedding target: {item}")
            records, stats = generator.generate(force=(force or config.force_reembed), max_nodes=max_nodes)
            updated = writer.write_embeddings(label, records)
            typer.echo(
                f"{label} embeddings: processed={stats.processed} skipped={stats.skipped} "
                f"failed={stats.failed} updated={updated}"
            )
            typer.echo(f"{label} generation details: {asdict(stats)}")


def _print_search_results(results: list) -> None:
    if not results:
        typer.echo("No results found.")
        return
    for index, result in enumerate(results, start=1):
        typer.echo(
            f"{index}. [{result.label}] id={result.node_id} "
            f"score={result.score:.4f} snippet={result.snippet} metadata={result.source_metadata}"
        )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
