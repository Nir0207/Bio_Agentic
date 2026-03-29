# HITL Plan

## Interrupt policy

Review can trigger when policy matches:
- low confidence evidence bundle
- contradictory signals
- too few citations
- high-stakes request marker/terms

## Approval/reject/edit flows

Resume payload supports:
- `{"action": "continue"}`
- `{"action": "reject"}`
- `{"action": "edit", "edits": {...}}`

Edit mode can annotate bundle warnings/gaps before finalization.

## Resumption behavior

Interrupt occurs in `request_human_review`.
On resume:
- `continue`: proceed to final payload
- `reject`: mark payload rejected with errors
- `edit`: apply requested edits then finalize

The workflow is checkpoint-ready via LangGraph checkpointer integration.
