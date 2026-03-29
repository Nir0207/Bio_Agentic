# verification runbook

## Verify Sample Payload

```bash
cd verification
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
python -m verification.app.cli verify sample
```

## Inspect Extracted Claims

```bash
python -m verification.app.cli inspect claims --input payloads/sample_orchestration_payload.json
```

## Inspect Verdict Summary

```bash
python -m verification.app.cli inspect verdict --input payloads/sample_orchestration_payload.json
```

## Run Full Flow

```bash
python -m verification.app.cli run all
```

## Re-run With Modified Payload

```bash
python -m verification.app.cli verify payload --input /absolute/path/to/custom_payload.json
```

## Common Verification Failures

- missing/invalid payload keys: input contract mismatch
- unresolved citation ids: provenance/citation coverage gaps
- score metadata missing: score claims downgraded to partial/unsupported
- contradictory graph/citation support: review-required path activated
