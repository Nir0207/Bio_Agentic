# verification phase

This phase is a standalone post-orchestration verifier that validates claims against already-retrieved evidence.

It consumes structured output from `orchestration/` and produces a verified payload with claim-level support statuses, citation/provenance checks, confidence scoring, and optional human-review gating.

## Why This Is Separate From Orchestration

`orchestration/` is responsible for retrieval, candidate assembly, and evidence bundle construction.

`verification/` is intentionally separate so it can:
1. validate claim correctness without owning retrieval
2. run deterministic checks over graph/citation/score evidence
3. enforce claim-policy and provenance coverage
4. trigger optional human review for risky outputs

## Upstream Dependency

Expected input is a structured orchestration payload containing:
- `normalized_query`
- `candidate_entities`
- `graph_evidence`
- `semantic_evidence`
- `model_scores`
- `provenance`
- `evidence_bundle`
- optional `draft_answer_text`

## Environment

Start from `verification/.env.example`.

Key settings:
- `ENABLE_HUMAN_REVIEW`
- `LOW_CONFIDENCE_THRESHOLD`
- `MIN_CITATIONS_PER_CLAIM`
- `REVIEW_ON_CONTRADICTION`
- `REVIEW_HIGH_STAKES`
- `SAMPLE_PAYLOAD_PATH`

## Exact Run Order

From project root:

```bash
cd verification
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"

python -m verification.app.cli verify sample
python -m verification.app.cli verify payload --input payloads/sample_orchestration_payload.json
python -m verification.app.cli inspect claims --input payloads/sample_orchestration_payload.json
python -m verification.app.cli inspect verdict --input payloads/sample_orchestration_payload.json
python -m verification.app.cli run all
```

If review is pending, resume with one of:

```bash
python -m verification.app.cli verify sample --review-action approve
python -m verification.app.cli verify sample --review-action reject
python -m verification.app.cli verify sample --review-action continue_with_caveats
python -m verification.app.cli verify sample --review-action edit --review-edits '{"claim_status_overrides": {"claim-001": "supported"}}'
```

## Docker Usage

This phase has its own Docker context and does not start Neo4j.

```bash
cd verification
cp .env.example .env

docker compose up --build --abort-on-container-exit --exit-code-from verification
```

Default command in compose/container:

```bash
python -m verification.app.cli verify sample
```

Compose behavior:
- one service only: `verification`
- source mounted for development (`../:/workspace`)
- local payload mount (`./payloads:/payloads`)
- `extra_hosts` includes `host.docker.internal`
