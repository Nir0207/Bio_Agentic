# hitl plan

## Review Trigger Conditions

Human review is triggered when one or more conditions are met:
- unsupported critical claims
- high-stakes query policy
- contradictory graph vs citation evidence
- insufficient citation coverage
- low overall confidence

## Review Actions

Supported actions:
- `approve`
- `reject`
- `edit`
- `continue_with_caveats`

## Action Semantics

- `approve`: accept output despite automated concerns
- `reject`: force overall verdict to `rejected`
- `edit`: apply explicit claim-status overrides from reviewer edits
- `continue_with_caveats`: proceed with caveated approval status

Pending review responses include claim ids and reasons so humans can focus on unresolved risk.
