# orchestration phase

This phase is the standalone orchestration layer that runs before final answer generation and before final verification.

It uses LangGraph to orchestrate:
1. query normalization and routing
2. graph retrieval (Neo4j)
3. semantic retrieval (existing embeddings outputs / vector or keyword mode)
4. model score retrieval (existing modeling outputs/properties)
5. candidate merge/ranking
6. evidence bundle construction
7. optional human-interrupt review
8. final structured payload for downstream answer/verification phases

This phase intentionally does **not** generate polished final prose answers and does **not** run final judgment/verification logic.

## Upstream dependencies

This phase consumes existing outputs and systems from:
- `embeddings/`
- `graphML/`
- `modeling/`

Neo4j remains the primary graph datastore.

## Environment

Start from `orchestration/.env.example`.

Key defaults:
- `NEO4J_URI=bolt://host.docker.internal:7688`
- `NEO4J_DATABASE=neo4j`
- `SEMANTIC_RETRIEVAL_MODE=keyword`
- `MODEL_SCORE_SOURCE=neo4j_property`
- `ENABLE_HUMAN_REVIEW=true`

Custom Neo4j port support is automatic via `NEO4J_URI`.

## Exact run order

From project root:

```bash
cd orchestration
python -m pip install -e ".[dev]"

# validate contracts and tool wiring
python -m orchestration.app.cli validate-tools

# inspect state transitions for a specific query
python -m orchestration.app.cli inspect-state --text "prioritize EGFR evidence"

# run one query
python -m orchestration.app.cli run query --text "prioritize EGFR evidence"

# run sample
python -m orchestration.app.cli run sample

# run dependency check + sample flow
python -m orchestration.app.cli run all
```

If review is triggered, resume in the same run invocation by supplying `--review-action`:

```bash
python -m orchestration.app.cli run query \
  --text "critical dose question for EGFR" \
  --high-stakes \
  --review-action continue
```

## Docker usage

This folder has its own Docker context and one service only (`orchestration`).

```bash
cd orchestration
cp .env.example .env

docker compose build orchestration
docker compose run --rm orchestration
```

Default container command:

```bash
python -m orchestration.app.cli run sample
```

The compose file includes:
- source mount for development (`../:/workspace`)
- `extra_hosts: host.docker.internal:host-gateway`
- `.env` loading

This folder does **not** start Neo4j or MLflow by default.
