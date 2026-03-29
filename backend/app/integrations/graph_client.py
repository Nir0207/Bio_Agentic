from __future__ import annotations

from app.utils.helpers import truncate_text


class GraphClient:
    def extract_candidate_entities(self, query: str) -> list[dict]:
        tokens = [part.strip(',.()') for part in query.split() if len(part.strip(',.()')) > 3]
        unique = []
        seen = set()
        for token in tokens:
            lowered = token.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            unique.append(token)
            if len(unique) >= 5:
                break

        return [
            {
                'entity_id': f'ENTITY_{idx+1}',
                'name': truncate_text(name, 40),
                'source': 'graphML',
                'relationship_hint': 'linked in pathway neighborhood',
            }
            for idx, name in enumerate(unique)
        ]
