# claim policy

## Supported Claim Types

- `entity_association`
- `pathway_participation`
- `similarity_claim`
- `evidence_strength_claim`
- `ranking_claim`

## Support Definitions

A claim is:
- `supported` when graph/citation/score checks are non-contradictory and materially aligned
- `partially_supported` when evidence exists but is incomplete, indirect, or weak
- `unsupported` when expected evidence is absent or contradictory
- `needs_review` when high-risk policy or contradiction triggers require human judgment

## Direct vs Indirect Support

Direct support requires relation metadata that aligns with claim semantics.

Indirect support means network/path context is present but should not be interpreted as proof of direct causality.

## Unsupported Handling Rules

Unsupported claims are always surfaced explicitly and contribute to:
- unsupported claim count
- confidence penalty
- warning list
- potential `review_required` / `rejected` verdicts
