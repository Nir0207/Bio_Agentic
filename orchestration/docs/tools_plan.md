# Tools Plan

## Tool list

- `get_subgraph_for_entity`
- `search_publications`
- `search_evidence`
- `get_model_score`
- `get_similar_entities`
- `get_pathway_context`
- `get_provenance_for_claim`

## Input/output contracts

Each tool wrapper has:
- typed request model
- typed response model
- `ToolExecutionMetadata` with start/end/status/rows/details

Outputs are structured pydantic objects used directly by nodes.

## Dependency boundaries

- graph datastore: Neo4j only
- semantic retrieval: existing embedding/vector outputs or deterministic keyword fallback
- model scoring: existing Neo4j writeback properties or modeling artifacts (no retraining)
- provenance: Neo4j-backed claim source traces

Tools are read-oriented and side-effect free by default.
