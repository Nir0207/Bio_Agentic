# verification phase goal

The goal of this phase is claim-by-claim validation over a structured evidence bundle from `orchestration/`.

## Verification Philosophy

1. Claims are extracted into structured objects.
2. Each claim is checked independently for graph support, citation support, and score consistency.
3. Deterministic checks are primary; prompts may assist extraction but do not override evidence rules.
4. Final status is computed per claim before any overall verdict is assigned.

## Graph Path Interpretation Rule

Graph paths are treated as network evidence, not automatic causality proof.

Direct support and indirect support are recorded separately:
- direct: relation metadata aligns with the claim type
- indirect: path/network context exists but causal strength is not implied

## Overall Verdict Model

Per-claim final statuses:
- `supported`
- `partially_supported`
- `unsupported`
- `needs_review`

Overall verdicts:
- `approved`
- `approved_with_caveats`
- `review_required`
- `rejected`

Human review can override automated outcomes when policy triggers are met.
