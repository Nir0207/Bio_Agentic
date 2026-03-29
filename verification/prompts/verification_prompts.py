from __future__ import annotations

VERIFICATION_ASSIST_PROMPT = """
Use structured evidence checks first.
Graph paths are support signals and must not be treated as automatic causal proof.
If evidence is weak or contradictory, mark claim for review.
""".strip()
