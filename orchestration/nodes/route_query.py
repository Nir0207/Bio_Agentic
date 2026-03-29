from __future__ import annotations

import re

from orchestration.app.constants import DEFAULT_INTENT
from orchestration.app.state import OrchestrationState, add_stage_metadata
from orchestration.prompts.router_prompts import ROUTER_RULES

TOKEN_RE = re.compile(r"[A-Za-z0-9_-]+")
ENTITY_RE = re.compile(r"\b[A-Z0-9][A-Z0-9-]{2,}\b")


def route_query_node(state: OrchestrationState) -> dict:
    user_query = str(state.get("user_query") or "").strip()
    normalized_query = " ".join(user_query.split())
    lower_query = normalized_query.lower()
    tokens = [token.lower() for token in TOKEN_RE.findall(normalized_query)]

    intent_type = _classify_intent(lower_query)

    entity_mentions = sorted(set(ENTITY_RE.findall(normalized_query)))
    # Keep route deterministic and bounded.
    target_entity_ids = entity_mentions[:5]

    execution_metadata = add_stage_metadata(
        state,
        "route_query",
        {
            "intent_type": intent_type,
            "mentions": target_entity_ids,
            "token_count": len(tokens),
        },
    )

    return {
        "normalized_query": normalized_query,
        "intent_type": intent_type,
        "target_entity_ids": target_entity_ids,
        "execution_metadata": execution_metadata,
    }


def _classify_intent(query_lower: str) -> str:
    if not query_lower:
        return DEFAULT_INTENT

    for intent, phrases in ROUTER_RULES.items():
        if any(phrase in query_lower for phrase in phrases):
            return intent

    return DEFAULT_INTENT
