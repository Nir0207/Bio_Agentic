# Feature Plan

## Feature Groups

Core numeric:
- `interaction_count`
- `pathway_count`
- `evidence_count`
- `publication_count`
- `avg_evidence_confidence`
- `max_evidence_confidence`
- `degree_centrality_like_count`

Optional numeric:
- `similar_to_neighbor_count`
- `avg_similarity_score`
- `semantic_similarity_avg`

Categorical:
- `community_id`

Embedding:
- `graph_embedding` flattened into deterministic columns (`graph_embedding_0...N`)

## Feature Schema Versioning

`FEATURE_SCHEMA_VERSION=protein_target_features_v1` is stored in:
- dataset metadata manifest
- feature manifest
- MLflow params

When feature logic changes, this version should be bumped.

## Embedding Flattening Approach

Graph embedding vectors are padded/truncated consistently during matrix build:
- max observed dimension in training set determines expanded columns
- missing dimensions are zero-filled
- inference reindexes to training manifest columns for strict compatibility

## Community Feature Handling

`community_id` is:
- null-safe normalized to string with `unknown` fallback
- one-hot encoded for sklearn-friendly matrices
- aligned to training-time columns during inference (new unseen categories become all-zero in known columns)
