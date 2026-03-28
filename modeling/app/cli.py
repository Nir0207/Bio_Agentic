from __future__ import annotations

import json
from pathlib import Path

import typer

from modeling.app.config import get_settings
from modeling.app.logging import configure_logging
from modeling.app.neo4j_client import Neo4jClient
from modeling.data.dataset_builder import build_dataset, load_latest_dataset
from modeling.inference.batch_predict import predict_batch, predict_for_protein_id
from modeling.inference.predictor import load_predictor
from modeling.training.persistence import build_writeback_payload, read_json, write_json, writeback_scores
from modeling.training.registry import register_model_from_run
from modeling.training.train import evaluate_latest_run, train_baseline_model
from modeling.validation.data_checks import run_data_checks
from modeling.validation.model_checks import validate_writeback_payload

app = typer.Typer(add_completion=False, help="Standalone modeling phase for local ML training and inference.")
dataset_app = typer.Typer(add_completion=False)
train_app = typer.Typer(add_completion=False)
evaluate_app = typer.Typer(add_completion=False)
register_app = typer.Typer(add_completion=False)
writeback_app = typer.Typer(add_completion=False)
run_app = typer.Typer(add_completion=False)

app.add_typer(dataset_app, name="dataset")
app.add_typer(train_app, name="train")
app.add_typer(evaluate_app, name="evaluate")
app.add_typer(register_app, name="register")
app.add_typer(writeback_app, name="writeback")
app.add_typer(run_app, name="run")


@dataset_app.command("build")
def dataset_build() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    with Neo4jClient.from_settings(settings) as client:
        client.verify_connectivity()
        result = build_dataset(settings, client=client)

    typer.echo(
        json.dumps(
            {
                "dataset_version": result.dataset_version,
                "dataset_path": str(result.dataset_path),
                "row_count": result.row_count,
                "splits": result.split_counts,
            },
            indent=2,
        )
    )


@dataset_app.command("inspect")
def dataset_inspect() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    frame, latest = load_latest_dataset(settings)
    checks = run_data_checks(frame, task_type=settings.task_type)

    output = {
        "dataset_version": latest["dataset_version"],
        "dataset_path": latest["dataset_path"],
        "rows": int(len(frame)),
        "columns": frame.columns.tolist(),
        "checks": checks,
    }
    typer.echo(json.dumps(output, indent=2))


@train_app.command("baseline")
def train_baseline() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    result = train_baseline_model(settings=settings)
    typer.echo(
        json.dumps(
            {
                "run_id": result.run_id,
                "dataset_version": result.dataset_version,
                "model_path": str(result.model_path),
                "metrics_path": str(result.metrics_path),
                "registry": (
                    {
                        "model_name": result.registry_result.model_name,
                        "model_version": result.registry_result.model_version,
                        "status": result.registry_result.status,
                    }
                    if result.registry_result
                    else None
                ),
            },
            indent=2,
        )
    )


@evaluate_app.command("latest")
def evaluate_latest() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    result = evaluate_latest_run(settings)
    typer.echo(json.dumps(result, indent=2))


@register_app.command("latest")
def register_latest() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    latest_training_path = settings.artifacts_root / "manifests" / "latest_training.json"
    if not latest_training_path.exists():
        raise typer.BadParameter("No latest training summary found. Run train baseline first.")

    latest = read_json(latest_training_path)
    registry_result = register_model_from_run(
        settings=settings,
        run_id=latest["run_id"],
        model_artifact_path="model",
        tags={
            "task_type": latest.get("task_type", settings.task_type),
            "dataset_version": latest.get("dataset_version", "unknown"),
            "manual_register": "true",
        },
    )

    if registry_result is None:
        typer.echo("Model registry is disabled (MLFLOW_REGISTER_MODEL=false).")
        raise typer.Exit(code=1)

    typer.echo(
        json.dumps(
            {
                "model_name": registry_result.model_name,
                "model_version": registry_result.model_version,
                "status": registry_result.status,
            },
            indent=2,
        )
    )


@app.command("predict")
def predict(protein_id: str = typer.Option(..., "--protein-id")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    result = predict_for_protein_id(settings, protein_id=protein_id)
    typer.echo(result.to_json(orient="records", indent=2))


@app.command("predict-batch")
def predict_batch_command(limit: int | None = typer.Option(None, "--limit")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    result = predict_batch(settings, limit=limit)

    output_path = settings.artifacts_root / "reports" / "latest_batch_predictions.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)

    typer.echo(
        json.dumps(
            {
                "row_count": int(len(result)),
                "output_path": str(output_path),
                "preview": result.head(10).to_dict(orient="records"),
            },
            indent=2,
        )
    )


@writeback_app.command("scores")
def writeback_scores_command(limit: int | None = typer.Option(None, "--limit")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    predictions = predict_batch(settings, limit=limit)
    predictor = load_predictor(settings)

    payload = build_writeback_payload(
        predictions=predictions,
        model_name=predictor.model_name,
        model_version=predictor.model_version,
        run_id=predictor.run_id,
    )
    validate_writeback_payload(payload)

    with Neo4jClient.from_settings(settings) as client:
        updated = writeback_scores(client, payload, batch_size=settings.writeback_batch_size)

    typer.echo(
        json.dumps(
            {
                "attempted": len(payload),
                "updated": updated,
                "model_name": predictor.model_name,
                "model_version": predictor.model_version,
                "run_id": predictor.run_id,
            },
            indent=2,
        )
    )


@run_app.command("all")
def run_all(writeback: bool | None = typer.Option(None, "--writeback/--no-writeback")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    with Neo4jClient.from_settings(settings) as client:
        client.verify_connectivity()
        dataset_result = build_dataset(settings, client=client)

    dataset, _ = load_latest_dataset(settings)
    dataset_checks = run_data_checks(dataset, task_type=settings.task_type)
    if dataset_checks["errors"]:
        raise typer.BadParameter(f"Dataset validation failed: {dataset_checks['errors']}")

    training_result = train_baseline_model(settings=settings)
    eval_result = evaluate_latest_run(settings)

    prediction_sample = predict_batch(settings, limit=10)
    prediction_sample_path = settings.artifacts_root / "reports" / "run_all_prediction_sample.csv"
    prediction_sample_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_sample.to_csv(prediction_sample_path, index=False)

    should_writeback = settings.writeback_scores if writeback is None else writeback
    writeback_summary: dict[str, object] | None = None
    if should_writeback:
        predictor = load_predictor(settings)
        full_predictions = predict_batch(settings)
        payload = build_writeback_payload(
            predictions=full_predictions,
            model_name=predictor.model_name,
            model_version=predictor.model_version,
            run_id=predictor.run_id,
        )
        validate_writeback_payload(payload)
        with Neo4jClient.from_settings(settings) as client:
            updated = writeback_scores(client, payload, batch_size=settings.writeback_batch_size)
        writeback_summary = {"attempted": len(payload), "updated": updated}

    summary = {
        "dataset_version": dataset_result.dataset_version,
        "dataset_rows": dataset_result.row_count,
        "dataset_split_counts": dataset_result.split_counts,
        "run_id": training_result.run_id,
        "model_type": training_result.model_type,
        "task_type": training_result.task_type,
        "metrics": eval_result["metrics"],
        "prediction_sample_path": str(prediction_sample_path),
        "registry": (
            {
                "model_name": training_result.registry_result.model_name,
                "model_version": training_result.registry_result.model_version,
                "status": training_result.registry_result.status,
            }
            if training_result.registry_result
            else None
        ),
        "writeback": writeback_summary,
    }

    summary_path = settings.artifacts_root / "manifests" / "run_all_summary.json"
    write_json(summary, summary_path)
    summary["summary_path"] = str(summary_path)

    typer.echo(json.dumps(summary, indent=2))


if __name__ == "__main__":
    app()
