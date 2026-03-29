# answering phase

## Phase Goal

Transform a machine-verified payload into user-facing answer outputs while preserving provenance.

Inputs come from `verification/`. Outputs are answer text, structured JSON, and evidence appendix.

## Verified-Payload-First Design

The phase only consumes verified payload fields and claim verdicts.

It does not perform:
- raw loading
- graph rebuilding
- semantic retrieval orchestration
- verification decisions
- model training

## Unsupported Claim Exclusion

Only claims with final status:
- `supported`
- `partially_supported`

are eligible for answer statements.

Unsupported claims are excluded from factual conclusions and may appear only as caveats or warnings.

## Fallback Mode Behavior

If LLM access is disabled or unavailable, fallback templates render all outputs from verified payload content.

Fallback still enforces:
- supported/partially-supported filtering
- deterministic citations
- caveat visibility
- review status surfacing
