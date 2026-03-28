from __future__ import annotations

import logging
from dataclasses import asdict

import typer

from gds.algorithms.fastrp_runner import run_fastrp
from gds.algorithms.knn_runner import run_knn
from gds.algorithms.leiden_runner import run_leiden
from gds.app.config import get_settings
from gds.app.logging import configure_logging
from gds.app.neo4j_client import Neo4jClient
from gds.projections.graph_projection import (
    create_or_reuse_projection,
    drop_graph,
    inspect_graph,
    list_graph_catalog,
)
from gds.projections.memory_estimation import (
    assert_estimate_safe,
    estimate_fastrp_memory,
    estimate_knn_memory,
    estimate_leiden_memory,
    estimate_projection_memory,
)
from gds.validation.gds_checks import format_validation_report, run_gds_validation_checks

logger = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="Standalone GDS pipeline for topology embeddings and communities.")
projection_app = typer.Typer(add_completion=False)
estimate_app = typer.Typer(add_completion=False)
run_app = typer.Typer(add_completion=False)

app.add_typer(projection_app, name="projection")
app.add_typer(estimate_app, name="estimate")
app.add_typer(run_app, name="run")


@projection_app.command("create")
def projection_create(
    replace: bool = typer.Option(False, "--replace", help="Drop and recreate named graph projection if it exists."),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    with Neo4jClient.from_settings(settings) as client:
        _ensure_gds_ready(client)
        projection_estimate = estimate_projection_memory(client, settings)
        assert_estimate_safe(projection_estimate)
        result = create_or_reuse_projection(client, settings, replace=replace)
    typer.echo(result.message)
    typer.echo(f"graph={result.graph_name} mode={result.mode} nodes={result.node_count} rels={result.relationship_count}")


@projection_app.command("list")
def projection_list() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    with Neo4jClient.from_settings(settings) as client:
        _ensure_gds_ready(client)
        entries = list_graph_catalog(client)

    if not entries:
        typer.echo("No in-memory GDS graphs found.")
        return

    for entry in entries:
        typer.echo(
            f"graph={entry.graph_name} db={entry.database} nodes={entry.node_count} "
            f"rels={entry.relationship_count} created={entry.creation_time}"
        )


@projection_app.command("inspect")
def projection_inspect(
    graph_name: str | None = typer.Option(
        None,
        "--graph-name",
        help="Named graph to inspect. Defaults to GDS_GRAPH_NAME from env.",
    ),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    target_graph = graph_name or settings.gds_graph_name

    with Neo4jClient.from_settings(settings) as client:
        _ensure_gds_ready(client)
        entry = inspect_graph(client, target_graph)

    if entry is None:
        typer.echo(f"GDS graph not found: {target_graph}")
        raise typer.Exit(code=1)

    typer.echo(
        f"graph={entry.graph_name} db={entry.database} nodes={entry.node_count} "
        f"rels={entry.relationship_count} created={entry.creation_time}"
    )
    typer.echo(f"schema={entry.schema}")


@projection_app.command("drop")
def projection_drop(
    graph_name: str | None = typer.Option(
        None,
        "--graph-name",
        help="Named graph to drop. Defaults to GDS_GRAPH_NAME from env.",
    ),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    target_graph = graph_name or settings.gds_graph_name

    with Neo4jClient.from_settings(settings) as client:
        _ensure_gds_ready(client)
        removed = drop_graph(client, target_graph)

    if removed:
        typer.echo(f"Dropped GDS graph: {target_graph}")
    else:
        typer.echo(f"GDS graph not found: {target_graph}")


@estimate_app.command("all")
def estimate_all() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    with Neo4jClient.from_settings(settings) as client:
        _ensure_gds_ready(client)
        projection_estimate = estimate_projection_memory(client, settings)
        estimates = [projection_estimate]
        typer.echo(_format_estimate_line(projection_estimate))

        fastrp_estimate = estimate_fastrp_memory(client, settings)
        estimates.append(fastrp_estimate)
        typer.echo(_format_estimate_line(fastrp_estimate))

        if settings.leiden_enabled:
            leiden_estimate = estimate_leiden_memory(client, settings)
            estimates.append(leiden_estimate)
            typer.echo(_format_estimate_line(leiden_estimate))

        if settings.knn_enabled:
            knn_estimate = estimate_knn_memory(client, settings)
            estimates.append(knn_estimate)
            typer.echo(_format_estimate_line(knn_estimate))

    failed = [estimate for estimate in estimates if estimate.insufficient_memory_warning or not estimate.within_threshold]
    if failed:
        raise typer.Exit(code=1)


@run_app.command("fastrp")
def run_fastrp_command() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    with Neo4jClient.from_settings(settings) as client:
        _ensure_gds_ready(client)
        _prepare_projection(client, settings, replace=False)
        estimate = estimate_fastrp_memory(client, settings)
        assert_estimate_safe(estimate)
        result = run_fastrp(client, settings)

    typer.echo(f"FastRP complete: {asdict(result)}")


@run_app.command("leiden")
def run_leiden_command() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    if not settings.leiden_enabled:
        typer.echo("Leiden is disabled (LEIDEN_ENABLED=false).")
        return

    with Neo4jClient.from_settings(settings) as client:
        _ensure_gds_ready(client)
        _prepare_projection(client, settings, replace=False)
        estimate = estimate_leiden_memory(client, settings)
        assert_estimate_safe(estimate)
        result = run_leiden(client, settings)

    typer.echo(f"Leiden complete: {asdict(result)}")


@run_app.command("knn")
def run_knn_command() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    if not settings.knn_enabled:
        typer.echo("KNN is disabled (KNN_ENABLED=false).")
        return

    with Neo4jClient.from_settings(settings) as client:
        _ensure_gds_ready(client)
        _prepare_projection(client, settings, replace=False)
        estimate = estimate_knn_memory(client, settings)
        assert_estimate_safe(estimate)
        result = run_knn(client, settings)

    typer.echo(f"KNN complete: {asdict(result)}")


@run_app.command("all")
def run_all() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    with Neo4jClient.from_settings(settings) as client:
        _ensure_gds_ready(client)
        projection_estimate = estimate_projection_memory(client, settings)
        assert_estimate_safe(projection_estimate)

        projection_result = create_or_reuse_projection(client, settings, replace=settings.gds_replace_graph)

        fastrp_estimate = estimate_fastrp_memory(client, settings)
        assert_estimate_safe(fastrp_estimate)
        fastrp_result = run_fastrp(client, settings)

        leiden_result = None
        leiden_estimate = None
        if settings.leiden_enabled:
            leiden_estimate = estimate_leiden_memory(client, settings)
            assert_estimate_safe(leiden_estimate)
            leiden_result = run_leiden(client, settings)

        knn_result = None
        knn_estimate = None
        if settings.knn_enabled:
            knn_estimate = estimate_knn_memory(client, settings)
            assert_estimate_safe(knn_estimate)
            knn_result = run_knn(client, settings)

        validation = run_gds_validation_checks(client, settings)

    typer.echo("GDS Summary")
    typer.echo("------------------")
    typer.echo(
        f"projection: graph={projection_result.graph_name} mode={projection_result.mode} "
        f"nodes={projection_result.node_count} rels={projection_result.relationship_count}"
    )
    typer.echo(_format_estimate_line(projection_estimate))
    typer.echo(_format_estimate_line(fastrp_estimate))
    typer.echo(f"fastrp: {asdict(fastrp_result)}")

    if settings.leiden_enabled and leiden_result is not None and leiden_estimate is not None:
        typer.echo(_format_estimate_line(leiden_estimate))
        typer.echo(f"leiden: {asdict(leiden_result)}")

    if settings.knn_enabled and knn_result is not None and knn_estimate is not None:
        typer.echo(_format_estimate_line(knn_estimate))
        typer.echo(f"knn: {asdict(knn_result)}")

    typer.echo(format_validation_report(validation))
    if validation.has_critical_issues:
        raise typer.Exit(code=1)


@app.command("validate")
def validate_only() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    with Neo4jClient.from_settings(settings) as client:
        _ensure_gds_ready(client)
        report = run_gds_validation_checks(client, settings)

    typer.echo(format_validation_report(report))
    if report.has_critical_issues:
        raise typer.Exit(code=1)


def _prepare_projection(client: Neo4jClient, settings, replace: bool) -> None:
    projection_estimate = estimate_projection_memory(client, settings)
    assert_estimate_safe(projection_estimate)
    create_or_reuse_projection(client, settings, replace=replace)


def _ensure_gds_ready(client: Neo4jClient) -> None:
    client.ensure_gds_available()


def _format_estimate_line(estimate) -> str:
    bytes_max_gb = f"{estimate.bytes_max_gb:.2f} GiB" if estimate.bytes_max_gb is not None else "unknown"
    return (
        f"estimate:{estimate.name} required={estimate.required_memory} "
        f"bytesMax={bytes_max_gb} threshold={estimate.threshold_bytes / (1024**3):.2f} GiB "
        f"safe={estimate.within_threshold and not estimate.insufficient_memory_warning}"
    )


if __name__ == "__main__":
    try:
        app()
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from None
