# Runbook

## Re-run Training End-to-End

```bash
python -m modeling.app.cli run all
```

## Inspect Latest Dataset and Checks

```bash
python -m modeling.app.cli dataset inspect
```

## Train Baseline Explicitly

```bash
python -m modeling.app.cli train baseline
python -m modeling.app.cli evaluate latest
```

## Disable Registry

Set env:
- `MLFLOW_REGISTER_MODEL=false`

Then run training normally. Model is still saved locally in modeling artifacts.

## Common Data-Quality Failures

- Missing `protein_id`/`label`/`split` columns
- Duplicate `protein_id` rows
- Single-class labels in classification mode
- Split leakage by overlapping `protein_id`
- Empty graph embeddings (warning; not always fatal)

## Safe Score Writeback

1. Train and validate first.
2. Run prediction batch:
```bash
python -m modeling.app.cli predict-batch
```
3. Write back explicitly:
```bash
python -m modeling.app.cli writeback scores
```

Writeback is batched `UNWIND` by `Protein.id` and only sets:
- `target_score`
- `target_score_model_name`
- `target_score_model_version`
- `target_score_run_id`
- `target_score_created_at`

Unrelated node properties are not modified.
