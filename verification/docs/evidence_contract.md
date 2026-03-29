# evidence contract

## Required Input Shape

Verification consumes a JSON payload containing:
- `normalized_query`
- `candidate_entities`
- `graph_evidence`
- `semantic_evidence`
- `model_scores`
- `provenance`
- `evidence_bundle`
- optional `draft_answer_text`

## Citation Expectations

Citation checks expect at least one of:
- citation ids in semantic evidence
- resolvable provenance references
- evidence/publication node identifiers

Citation ids should be resolvable back to publication/evidence references and semantically related to claim targets.

## Score Metadata Expectations

Score blocks should include:
- `candidate_id`
- `score_name`
- `score_value`
- `model_name`
- `model_version`

Missing model metadata degrades support confidence for score-based claims.
