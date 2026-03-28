# Modeling Phase

`modeling` is a standalone ML phase that trains and serves protein target prioritization models from already-prepared Neo4j graph properties.

## Purpose

This phase:
- extracts model features from Neo4j (`Protein` + related graph aggregates)
- builds local tabular datasets and deterministic train/validation/test splits
- trains baseline classical ML models (scikit-learn first, optional XGBoost)
- tracks runs, metrics, params, and artifacts in MLflow
- optionally registers models to MLflow Model Registry
- supports local inference and optional prediction writeback to Neo4j

This phase does **not** implement:
- LangGraph or agents
- LLM answer generation
- judgment/verification layer
- final GraphRAG answer flow
- frontend/UI
- data loading, graph rebuilding, embedding generation, or GDS execution

## Dependencies on Earlier Phases

`modeling` assumes both of these are already completed:
- `embeddings` phase (semantic/vector properties already present where relevant)
- `graphML` phase (graph embedding/community outputs already written to Neo4j)

This phase only consumes existing graph state and graph-derived properties.

## Why This Comes Before Agents/LLM

Classical ML scoring gives deterministic, measurable baselines (metrics + model versions) before adding agentic orchestration or answer-generation complexity.

## Environment

Copy `.env.example` to `.env` and set values.

Supported variables:
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`
- `MLFLOW_TRACKING_URI`
- `MLFLOW_EXPERIMENT_NAME`
- `MLFLOW_REGISTER_MODEL`
- `MODEL_REGISTRY_NAME`
- `MODEL_TYPE`
- `TASK_TYPE`
- `LABEL_STRATEGY`
- `TRAIN_TEST_SEED`
- `TEST_SIZE`
- `VALIDATION_SIZE`
- `ENABLE_XGBOOST`
- `WRITEBACK_SCORES`
- `LOG_LEVEL`

## Run Order

Standard pipeline (`python -m modeling.app.cli run all`):
1. Build dataset from Neo4j features
2. Validate dataset
3. Train baseline model
4. Evaluate latest run
5. Log to MLflow
6. Register model (if enabled)
7. Run prediction sample
8. Optionally write scores back to Neo4j
9. Print compact summary

## CLI

```bash
python -m modeling.app.cli dataset build
python -m modeling.app.cli dataset inspect
python -m modeling.app.cli train baseline
python -m modeling.app.cli evaluate latest
python -m modeling.app.cli register latest
python -m modeling.app.cli predict --protein-id P00533
python -m modeling.app.cli predict-batch
python -m modeling.app.cli writeback scores
python -m modeling.app.cli run all
```

## Docker

This phase has its own Docker context and a single service (`modeling`).
It does not launch Neo4j or MLflow.

```bash
cd modeling
cp .env.example .env

docker compose build modeling
docker compose run --rm modeling
```

Default container command:
- `python -m modeling.app.cli run all`

## Custom Neo4j Port Notes

For host Neo4j on a custom Bolt port, set `NEO4J_URI` explicitly. Docker default example is:
- `bolt://host.docker.internal:7688`

For local host execution you can use:
- `bolt://localhost:7688`

## MLflow Notes

Tracking is fully env-driven via `MLFLOW_TRACKING_URI` and `MLFLOW_EXPERIMENT_NAME`.
Model Registry usage requires:
- `MLFLOW_REGISTER_MODEL=true`
- registry-capable, database-backed MLflow backend store.
