# Modeling Phase Goal

This phase introduces a standalone model-development workflow that consumes already-populated Neo4j graph state and produces trainable/tabular datasets, baseline ML models, tracked experiments, and optional score writeback.

## Inputs Used from Neo4j

Primary Protein-centered feature inputs:
- `Protein.graph_embedding`
- `Protein.community_id`
- Protein interaction counts (`INTERACTS_WITH`)
- Pathway participation counts (`PARTICIPATES_IN`)
- Evidence aggregate counts/confidence (`SUPPORTS`)
- Publication aggregate counts (`MENTIONS`)
- Optional similarity aggregates (`SIMILAR_TO`) when graphML KNN is enabled
- Optional semantic aggregate side signals when already represented numerically

This phase does not regenerate embeddings or execute GDS.

## Labeling Strategy Limitations

Current labels are heuristic (pseudo-labels), not curated gold labels. This supports rapid baseline iteration but should not be treated as production truth.

Implemented modes:
- heuristic score (`heuristic_score`)
- heuristic binary labels (`heuristic_binary`)
- task-aware fallback conversions between score/binary based on `TASK_TYPE`

Label formulas and parameters are persisted and logged to MLflow for traceability.

## Why Baselines First

Baseline classical ML models provide:
- deterministic metrics
- versioned experiment history
- fast iteration on feature value
- low coupling to agent/LLM layers

This allows us to harden data and scoring foundations before adding downstream orchestration and answer-generation complexity.
