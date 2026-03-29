from __future__ import annotations


def citation_rules_prompt() -> str:
    return (
        "Citation rules: "
        "1) Keep existing tags unchanged. "
        "2) Do not invent citations. "
        "3) Attach at least one citation tag to each material claim sentence. "
        "4) Preserve distinction between direct and indirect support when caveating."
    )
