# Runbook

## Run a sample query

```bash
cd orchestration
python -m pip install -e ".[dev]"
python -m orchestration.app.cli run sample
```

## Inspect state transitions

```bash
python -m orchestration.app.cli inspect-state --text "prioritize EGFR evidence"
```

## Resume from interrupt

Trigger review (example high-stakes):

```bash
python -m orchestration.app.cli run query \
  --text "critical dose question for EGFR" \
  --high-stakes
```

Resume in same invocation pattern:

```bash
python -m orchestration.app.cli run query \
  --text "critical dose question for EGFR" \
  --high-stakes \
  --review-action continue
```

Reject path:

```bash
python -m orchestration.app.cli run query \
  --text "critical dose question for EGFR" \
  --high-stakes \
  --review-action reject
```

Edit path:

```bash
python -m orchestration.app.cli run query \
  --text "critical dose question for EGFR" \
  --high-stakes \
  --review-action edit \
  --review-edits '{"bundles": {"EGFR": {"warnings": ["manual_note"]}}}'
```

## Common tool failure cases

- Neo4j unavailable: service falls back to deterministic mock data when enabled.
- Vector retrieval unavailable: semantic service falls back to keyword retrieval.
- Missing model artifacts/properties: scoring falls back to available source or empty/default score.
- Empty evidence links: bundle carries unresolved gaps and can trigger review.
