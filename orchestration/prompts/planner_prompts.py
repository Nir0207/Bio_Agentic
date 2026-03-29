from __future__ import annotations

PLANNER_RULES = {
    "default": "Run graph + semantic + scoring and merge deterministically",
    "target_prioritization": "Favor model scores and graph centrality context",
    "pathway_exploration": "Favor pathway context and graph relation chains",
    "evidence_lookup": "Favor publication/evidence semantic hits and provenance",
    "similarity_lookup": "Favor nearest graph neighbors and semantic similarity",
}
