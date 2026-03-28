# Model Plan

## Supported Model Types

- `logistic_regression` (classification only)
- `random_forest` (classifier/regressor)
- `gradient_boosting` via HistGradientBoosting (classifier/regressor)
- `xgboost` (optional, gated by `ENABLE_XGBOOST=true`)

## Task Modes

- `TASK_TYPE=classification`
: classification metrics + probability-aware scoring where available.

- `TASK_TYPE=regression`
: continuous score prediction with regression metrics.

## Default Baseline Choices

Default env values:
- `MODEL_TYPE=logistic_regression`
- `TASK_TYPE=classification`
- `LABEL_STRATEGY=heuristic_binary`

This keeps default runs scikit-learn-only and low-friction.

## Future Extensions

Planned evolution after baseline stabilization:
- calibrated probability models
- rank-oriented objectives/metrics
- curated label integration
- multi-target training (`evidence_strength`, `pathway_relevance`)
- richer feature families and temporal features
