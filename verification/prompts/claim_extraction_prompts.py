from __future__ import annotations

CLAIM_EXTRACTION_SYSTEM_PROMPT = """
Extract atomic claims and return structured JSON only.
Use claim types from the verification policy.
Do not infer causality from network links alone.
""".strip()

CLAIM_EXTRACTION_USER_PROMPT = """
Given draft answer text and evidence summaries, emit claims with:
- claim_id
- claim_text
- claim_type
- target_entity_ids
- directness_level
- source_span (if available)
""".strip()
