# citation policy

## Citation Formatting Rules

Citations are deterministic and ordered by first appearance across supported/partially-supported claims.

Tags use stable incremental form:
- `[C1]`, `[C2]`, ...

## Citation Type Coverage

Supported source kinds:
- publication references (for example PMID/DOI)
- evidence node references
- graph-path references
- model score references

## Graph-Path Citation Handling

Graph path IDs from verified verdicts are mapped into citation entries and appendix graph items.

Optional enrichment can add display metadata from Neo4j, but cannot change claim support status.

## Partially Supported Claims

Partially supported claims must be explicitly qualified in rendered output and still carry citations.

## Caveat Rendering Rules

Missing evidence and review-status warnings must be surfaced as caveats and unresolved gaps.
