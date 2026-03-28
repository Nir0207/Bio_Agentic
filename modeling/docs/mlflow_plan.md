# MLflow Plan

## Tracked Params

Each training run logs:
- `model_type`
- `task_type`
- `label_strategy`
- `feature_schema_version`
- `dataset_version`
- train/validation/test row counts
- model hyperparameters

## Tracked Metrics

Classification:
- accuracy
- precision
- recall
- f1
- roc_auc (when score/probability is available)

Regression:
- rmse
- mae
- r2

## Artifacts Logged

- dataset metadata snapshot
- split manifest
- feature manifest (column list/schema)
- metrics JSON
- feature importance CSV (if available)
- confusion matrix or residual diagnostic plot
- sample predictions CSV
- model package (`mlflow.sklearn.log_model`)

## Registry Behavior

When `MLFLOW_REGISTER_MODEL=true`:
- run model artifact is registered under `MODEL_REGISTRY_NAME`
- model version tags are added
- alias update attempted (default alias: `latest`)

## Registry Backend Note

MLflow Model Registry requires a registry-capable backend store (database-backed MLflow setup). File-only local backends usually cannot provide production-grade registry behavior.
