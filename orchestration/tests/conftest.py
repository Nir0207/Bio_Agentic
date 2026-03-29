from __future__ import annotations

import pytest

from orchestration.app.config import Settings
from orchestration.app.graph_builder import OrchestrationRuntime, build_graph
from orchestration.services.evidence_service import EvidenceService
from orchestration.services.scoring_service import ScoringService
from orchestration.services.semantic_service import SemanticService
from orchestration.tools.evidence_tools import EvidenceTools
from orchestration.tools.neo4j_tools import Neo4jTools
from orchestration.tools.scoring_tools import ScoringTools
from orchestration.tools.semantic_search_tools import SemanticSearchTools


class FakeNeo4jService:
    def __init__(self) -> None:
        self.allow_mock_fallback_data = True

    def close(self) -> None:
        return None

    def verify_connectivity(self) -> dict:
        return {"ok": True, "uri": "fake://neo4j"}

    def resolve_entities_by_text(self, text: str, top_k: int = 5) -> list[dict]:
        return [{"candidate_id": "EGFR", "candidate_type": "Protein", "display_name": "EGFR"}]

    def get_subgraph_for_entity(self, entity_id: str, max_hops: int = 2, max_paths: int = 4) -> list[dict]:
        return [
            {
                "candidate_id": entity_id,
                "candidate_type": "Protein",
                "path_summary": f"{entity_id} -> MAPK",
                "nodes": [
                    {"node_id": entity_id, "node_labels": ["Protein"], "display_name": entity_id},
                    {"node_id": "MAPK", "node_labels": ["Pathway"], "display_name": "MAPK Pathway"},
                ],
                "edges": [
                    {
                        "edge_id": f"edge:{entity_id}",
                        "relation_type": "PARTICIPATES_IN",
                        "source_node_id": entity_id,
                        "target_node_id": "MAPK",
                        "confidence": 0.7,
                        "source_system": "fake",
                    }
                ],
                "relation_types": ["PARTICIPATES_IN"],
                "supporting_source_systems": ["fake"],
                "confidence": 0.7,
                "source_metadata": {"source_system": "fake"},
            }
        ]

    def get_similar_entities(self, entity_id: str, top_k: int = 5) -> list[dict]:
        return [
            {
                "candidate_id": "ERBB2",
                "candidate_type": "Protein",
                "display_name": "ERBB2",
                "similarity": 0.82,
            }
        ]

    def get_pathway_context(self, entity_id: str, top_k: int = 5) -> list[dict]:
        return self.get_subgraph_for_entity(entity_id)

    def search_publications_keyword(self, query_text: str, top_k: int = 5) -> list[dict]:
        return [
            {
                "node_id": "PUB1",
                "node_type": "Publication",
                "title": "EGFR inhibition evidence",
                "snippet": "EGFR response in pathway models.",
                "score": 0.9,
                "source": "pubmed",
                "citation_handle": "PMID:1",
            }
        ]

    def search_evidence_keyword(self, query_text: str, top_k: int = 5) -> list[dict]:
        return [
            {
                "node_id": "EVI1",
                "node_type": "Evidence",
                "title": None,
                "snippet": "EGFR signal evidence.",
                "score": 0.88,
                "source": "internal",
                "citation_handle": "EVI-CIT-1",
                "linked_candidate_id": "EGFR",
            }
        ]

    def search_publications_vector(self, query_embedding: list[float], index_name: str, top_k: int = 5) -> list[dict]:
        return self.search_publications_keyword("vector", top_k)

    def search_evidence_vector(self, query_embedding: list[float], index_name: str, top_k: int = 5) -> list[dict]:
        return self.search_evidence_keyword("vector", top_k)

    def get_model_score_from_neo4j(self, entity_id: str, score_props: dict[str, str]) -> dict:
        score = 0.82 if entity_id == "EGFR" else 0.4
        return {
            "candidate_id": entity_id,
            "score_value": score,
            "model_name": "test_model",
            "model_version": "1",
            "run_id": "run-1",
            "timestamp": "2026-01-01T00:00:00Z",
        }

    def get_provenance_for_claim(self, candidate_id: str, citation_ids: list[str]) -> list[dict]:
        ids = citation_ids or [f"fallback:{candidate_id}"]
        return [
            {
                "claim_id": candidate_id,
                "source_system": "publication",
                "source_ref": item,
                "retrieved_at": "2026-01-01T00:00:00Z",
                "metadata": {"source_name": "fake"},
            }
            for item in ids
        ]


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        semantic_retrieval_mode="keyword",
        enable_human_review=True,
        hitl_low_confidence_threshold=0.4,
        hitl_min_citations=1,
        allow_mock_fallback_data=True,
    )


@pytest.fixture
def runtime(settings: Settings) -> OrchestrationRuntime:
    neo4j = FakeNeo4jService()
    semantic = SemanticService(neo4j_service=neo4j, retrieval_mode="keyword")
    scoring = ScoringService(neo4j_service=neo4j, score_source="neo4j_property", score_name="target_score")
    evidence = EvidenceService()

    return OrchestrationRuntime(
        settings=settings,
        neo4j_service=neo4j,
        semantic_service=semantic,
        scoring_service=scoring,
        evidence_service=evidence,
        neo4j_tools=Neo4jTools(neo4j),
        semantic_tools=SemanticSearchTools(semantic),
        scoring_tools=ScoringTools(scoring),
        evidence_tools=EvidenceTools(neo4j),
    )


@pytest.fixture
def graph(runtime: OrchestrationRuntime):
    compiled, _ = build_graph(runtime=runtime)
    return compiled
