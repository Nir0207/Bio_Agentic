from __future__ import annotations

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import typer
from neo4j import GraphDatabase

from app.config import get_settings
from app.logging import configure_logging
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

app.add_typer(download_app, name="download")
app.add_typer(load_app, name="load")
app.add_typer(neo4j_app, name="neo4j")
app.add_typer(transform_app, name="transform")
app.add_typer(run_app, name="run")


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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
