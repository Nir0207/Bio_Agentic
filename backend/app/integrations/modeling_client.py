from __future__ import annotations


class ModelingClient:
    def score_candidates(self, candidates: list[dict]) -> list[dict]:
        scored: list[dict] = []
        for idx, item in enumerate(candidates):
            score = round(max(0.45, 0.9 - (idx * 0.08)), 3)
            scored.append({**item, 'score': score, 'model': 'modeling'})
        return scored
