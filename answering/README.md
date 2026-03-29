# answering phase

This phase is a standalone post-verification answer generator.

It consumes verified payloads from `verification/` and produces:
1. final answer text
2. structured answer JSON
3. citation-aware evidence appendix

## Why This Is Separate From Verification

`verification/` decides claim support and truth status.

`answering/` is intentionally separate so it can:
1. render user-facing output without re-running verification
2. preserve claim-level provenance and citations
3. support answer style controls without changing verdict logic
4. degrade safely to non-LLM rendering when providers are unavailable

## Upstream Dependency

Expected input is a verified payload containing:
- `original_query`
- `candidate_entities`
- `extracted_claims`
- `claim_verdicts`
- `overall_verdict`
- `overall_confidence`
- `supporting_evidence_index`
- `missing_evidence_index`
- `warnings`
- `review_status`
- `final_verified_payload_version`

## Environment

Use `answering/.env.example` as a local template.

Key settings:
- `ANSWER_STYLE`
- `ANSWERING_PROVIDER`
- `ANSWERING_MODEL_NAME`
- `ANSWERING_TEMPERATURE`
- `ANSWERING_TIMEOUT_SECONDS`
- `ANSWERING_USE_FALLBACK_ONLY`
- `ENABLE_OPTIONAL_ENRICHMENT`
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`
- `LOG_LEVEL`

Provider fields for hosted backends are available in config:
- `ANSWERING_API_KEY`, `ANSWERING_BASE_URL`
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_API_VERSION`
- `ANTHROPIC_BASE_URL`, `ANTHROPIC_API_KEY`
- `OLLAMA_BASE_URL`

## Exact Run Order

From project root:

```bash
cd answering
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"

python -m answering.app.cli answer --input payloads/sample_verified_payload.json
python -m answering.app.cli answer sample
python -m answering.app.cli render markdown --input payloads/sample_verified_payload.json
python -m answering.app.cli render json --input payloads/sample_verified_payload.json
python -m answering.app.cli render appendix --input payloads/sample_verified_payload.json
python -m answering.app.cli run all
```

## Docker Usage

This phase has its own Docker context and does not start Neo4j.

```bash
cd answering
cp .env.example .env

docker compose up --build --abort-on-container-exit --exit-code-from answering
```

Default command in compose/container:

```bash
python -m answering.app.cli answer sample
```

Compose behavior:
- one service only: `answering`
- source mounted for development (`../:/workspace`)
- local payload mount (`./payloads:/payloads`)
- `extra_hosts` includes `host.docker.internal`

## Optional Enrichment

Optional enrichment is display-only and disabled by default:
- enable with `ENABLE_OPTIONAL_ENRICHMENT=true`
- uses `NEO4J_URI` (default `bolt://host.docker.internal:7688`)
- never alters verification verdicts or claim truth status
