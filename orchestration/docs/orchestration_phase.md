# Orchestration Phase

## Phase goal

Build an answer-ready structured payload by orchestrating graph retrieval, semantic retrieval, and model scoring in a deterministic workflow with optional human checkpoints.

## LangGraph role in the stack

LangGraph is the runtime and state orchestrator for this phase:
- explicit typed shared state
- small node-level execution units
- tool-oriented node boundaries
- checkpoint/interrupt-ready workflow

## State design

The shared state tracks:
- `user_query`, `normalized_query`, `intent_type`
- `target_entity_ids`, `candidate_entities`
- `graph_evidence`, `semantic_evidence`, `model_scores`
- `provenance`, `evidence_bundle`
- `needs_human_review`, `review_reason`
- `final_payload`, `errors`, `execution_metadata`

## Why output is structured payload (not final prose)

This phase intentionally produces structured evidence objects so downstream answering and verification can reason over:
- explicit graph paths
- citation-backed semantic evidence
- model scoring provenance
- confidence summaries and unresolved gaps

This separation keeps orchestration deterministic, inspectable, and easy to review before final narrative generation.
