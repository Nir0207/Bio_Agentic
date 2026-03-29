# prompt plan

## Prompt Sections

1. system policy
- no new claims
- use only supported/partially_supported claims
- preserve citation tags

2. citation policy
- every material claim sentence must include provided citation tags
- no citation invention

3. style instruction
- concise, detailed, or technical guidance

4. serialized verified context
- query
- verdict/confidence
- approved claim blocks
- missing evidence
- warnings

## Style Handling

`ANSWER_STYLE` controls verbosity and structure:
- concise: short output and compact caveats
- detailed: structured findings plus explicit caveats
- technical: directness qualifiers and stronger evidence detail

## Grounding Rules

Prompt content is built strictly from verified payload claims and evidence IDs.

Unsupported claims are never passed as answer candidates.

## No-New-Claims Rule

The model is instructed to avoid adding entities, mechanisms, or outcomes not explicitly present in verified claim blocks.
