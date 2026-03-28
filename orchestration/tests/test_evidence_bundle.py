from __future__ import annotations

from orchestration.nodes.finalize_payload import finalize_payload_node
from orchestration.schemas.candidate_models import CandidateEntity
from orchestration.schemas.evidence_models import GraphPath, ModelScore, SemanticHit
from orchestration.services.evidence_service import EvidenceService
from orchestration.tools.neo4j_tools import SubgraphRequest
from orchestration.tools.scoring_tools import ModelScoreRequest
from orchestration.tools.semantic_search_tools import EvidenceSearchRequest


def test_candidate_merge_logic_prefers_stronger_combined_signals() -> None:
    service = EvidenceService()

    graph_candidates = [
        CandidateEntity(candidate_id="EGFR", candidate_type="Protein", graph_support=0.9, sources=["graph"]),
        CandidateEntity(candidate_id="ALK", candidate_type="Protein", graph_support=0.3, sources=["graph"]),
    ]
    semantic_hits = [
        SemanticHit(
            node_id="EVI1",
            node_type="Evidence",
            retrieval_score=0.85,
            snippet="EGFR evidence",
            citation_handle="PMID:1",
            linked_candidate_ids=["EGFR"],
        )
    ]
    model_scores = [
        ModelScore(candidate_id="EGFR", score_name="target_score", score_value=0.8),
        ModelScore(candidate_id="ALK", score_name="target_score", score_value=0.2),
    ]

    merged = service.merge_candidates(graph_candidates, semantic_hits, model_scores)

    assert merged[0].candidate_id == "EGFR"
    assert merged[0].rank_score >= merged[1].rank_score


def test_evidence_bundle_shape_contains_required_fields(runtime) -> None:
    service = runtime.evidence_service
    candidate = CandidateEntity(candidate_id="EGFR", candidate_type="Protein", sources=["graph"])
    graph_paths = runtime.neo4j_tools.get_subgraph_for_entity(SubgraphRequest(entity_id="EGFR")).graph_paths
    semantic_hits = runtime.semantic_tools.search_evidence(EvidenceSearchRequest(query_text="EGFR evidence")).hits
    model_score = runtime.scoring_tools.get_model_score(ModelScoreRequest(candidate_id="EGFR")).model_score

    bundle = service.build_evidence_bundle(
        candidate=candidate,
        graph_paths=graph_paths,
        semantic_hits=semantic_hits,
        model_scores=[model_score] if model_score else [],
        neo4j_service=runtime.neo4j_service,
    )

    assert bundle.candidate_id == "EGFR"
    assert isinstance(bundle.citation_ids, list)
    assert bundle.confidence_summary.overall_confidence >= 0.0


def test_finalize_payload_structure() -> None:
    state = {
        "user_query": "prioritize EGFR",
        "normalized_query": "prioritize egfr",
        "intent_type": "target_prioritization",
        "target_entity_ids": ["EGFR"],
        "candidate_entities": [CandidateEntity(candidate_id="EGFR", candidate_type="Protein")],
        "graph_evidence": [
            GraphPath(
                candidate_id="EGFR",
                candidate_type="Protein",
                path_summary="EGFR -> MAPK",
                nodes=[],
                edges=[],
                relation_types=[],
                confidence=0.5,
                source_metadata={},
                supporting_source_systems=[],
            )
        ],
        "semantic_evidence": [
            SemanticHit(
                node_id="E1",
                node_type="Evidence",
                retrieval_score=0.7,
                snippet="evidence",
                citation_handle="C1",
                linked_candidate_ids=["EGFR"],
            )
        ],
        "model_scores": [ModelScore(candidate_id="EGFR", score_name="target_score", score_value=0.9)],
        "provenance": [],
        "evidence_bundle": [],
        "errors": [],
        "execution_metadata": {"stages": [], "tool_runs": []},
    }

    out = finalize_payload_node(state)
    payload = out["final_payload"]

    assert payload["normalized_query"] == "prioritize egfr"
    assert payload["candidate_entities"][0]["candidate_id"] == "EGFR"
    assert payload["status"] == "ready"
